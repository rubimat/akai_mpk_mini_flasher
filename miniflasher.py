import os
import mido
import json
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Dict

READ_HEADER = [0x47, 0x7F, 0x7C, 0x63, 0x00, 0x01]
WRITE_HEADER = [0x47, 0x7F, 0x7C, 0x61, 0x00, 0x01]

class ReadWrite(Enum):
    READ = 'r'
    WRITE = 'w'

class ValidArgs:
    read_write: ReadWrite
    preset_no: int
    filepath: str

    def __init__(self, read_write: str, preset_no: int, filepath: str) -> None:
        if read_write not in ['r', 'w']:
            raise ValueError("The read_write argument must be either 'r' or 'w'.")
        self.read_write = ReadWrite(read_write)

        if int(preset_no) not in range(1,5):
            raise ValueError('The preset_number argument must be an integer between 1 and 4.')
        self.preset_no = int(preset_no)

        preset_path = os.path.join(filepath)
        if not preset_path.endswith('.json'):
            raise FileNotFoundError('The filepath argument must be a valid path to a JSON file.')
        self.filepath = preset_path

@dataclass(frozen=True)
class IOPorts:
    inport: Any
    outport: Any

def init_io() -> IOPorts:
    return IOPorts(mido.Backend().open_input('MPK mini'),
                   mido.Backend().open_output('MPK mini'))

def read_preset_bytes(io: IOPorts, preset_no: int) -> List[int]:
    if preset_no not in range(1,5):
        raise ValueError('The preset index must be an integer between 1 and 4.')
    payload_header = READ_HEADER + [preset_no]
    msg = mido.Message('sysex', data=payload_header)
    io.outport.send(msg)
    in_msg = io.inport.receive()
    return in_msg.bytes()[len(payload_header)+1:-1]

def write_preset_bytes(io: IOPorts, preset_no: int, bytes_data: List[int]) -> None:
    if len(bytes_data) != 101:
        raise ValueError('The bytes_data must be a list of 101 integers.')
    payload_header = WRITE_HEADER + [preset_no]
    payload = payload_header + bytes_data
    out_msg = mido.Message('sysex', data=payload)
    io.outport.send(out_msg)

def to_dict_struct(byte_data: List[int]) -> Dict[str, Any]:
    if len(byte_data) != 101:
        raise ValueError('The byte_data must be a list of 101 integers.')
    output = {
        'pad_midi_ch': byte_data[0],
        'key_knob_midi_ch': byte_data[1],
        'octave': byte_data[2],
        'transposition': byte_data[3],
        'arpeggio': {
            'enable': byte_data[4],
            'mode': byte_data[5],
            'time_division': byte_data[6],
            'clock': byte_data[7],
            'latch': byte_data[8],
            'tempo_taps': byte_data[9],
            'tempo_bpm': (byte_data[10]*128 + byte_data[11]),
            'octave': byte_data[12],
        },
        'pad_bank_1': [
            {'pad_no': i,
            'note': byte_data[13 + 4*i],
            'pc': byte_data[13 + 4*i + 1],
            'cc': byte_data[13 + 4*i + 2],
            'type': byte_data[13 + 4*i + 3]} for i in range(8)
        ],
        'pad_bank_2': [
            {'pad_no': i,
            'note': byte_data[45 + 4*i],
            'pc': byte_data[45 + 4*i + 1],
            'cc': byte_data[45 + 4*i + 2],
            'type': byte_data[45 + 4*i + 3]} for i in range(8)
        ],
        'knobs': [
            {'knob_no': i,
            'cc': byte_data[77 + 3*i],
            'low': byte_data[77 + 3*i + 1],
            'high': byte_data[77 + 3*i + 2]} for i in range(8)
        ]
    }
    return output

def to_byte_struct(dict_data: Dict[str, Any]) -> List[int]:
    output = [
        dict_data['pad_midi_ch'],
        dict_data['key_knob_midi_ch'],
        dict_data['octave'],
        dict_data['transposition'],
        dict_data['arpeggio']['enable'],
        dict_data['arpeggio']['mode'],
        dict_data['arpeggio']['time_division'],
        dict_data['arpeggio']['clock'],
        dict_data['arpeggio']['latch'],
        dict_data['arpeggio']['tempo_taps'],
        dict_data['arpeggio']['tempo_bpm']//128,
        dict_data['arpeggio']['tempo_bpm']%128,
        dict_data['arpeggio']['octave'],
    ]

    for i in range(8):
        pad_data = [dict_data['pad_bank_1'][i]['note'],
                    dict_data['pad_bank_1'][i]['pc'],
                    dict_data['pad_bank_1'][i]['cc'],
                    dict_data['pad_bank_1'][i]['type']]
        output += pad_data

    for i in range(8):
        pad_data = [dict_data['pad_bank_2'][i]['note'],
                    dict_data['pad_bank_2'][i]['pc'],
                    dict_data['pad_bank_2'][i]['cc'],
                    dict_data['pad_bank_2'][i]['type']]
        output += pad_data

    for i in range(8):
        knob_data = [dict_data['knobs'][i]['cc'],
                    dict_data['knobs'][i]['low'],
                    dict_data['knobs'][i]['high']]
        output += knob_data

    return output

def store_preset_json(preset_dict: Dict[str, Any], valid_args: ValidArgs) -> None:
    res = ''
    # If file exists asks user for permission to overwrite.
    if os.path.isfile(valid_args.filepath):
        while res not in ['y', 'n', 'Y', 'N']:
            res = str(input("Overwrite the preset "+valid_args.filepath+"? [y/n]"))
        if res in ['n', 'N']:
            print("Reading aborted.")
            return
    json.dump(preset_dict, open(valid_args.filepath, 'w'), indent=2)
    print("Successfully stored the preset number "+str(valid_args.preset_no)+" to "+valid_args.filepath+".")

def load_preset_json(valid_args: ValidArgs) -> Dict[str, Any]:
    preset_dict = json.load(open(valid_args.filepath, 'r'))
    if preset_dict['pad_midi_ch'] not in range(0,16):
        raise ValueError('The pad_midi_ch must be an integer between 0 and 15.')
    if preset_dict['key_knob_midi_ch'] not in range(0,16):
        raise ValueError('The key_knob_midi_ch must be an integer between 0 and 15.')
    if preset_dict['octave'] not in range(0,9):
        raise ValueError('The octave must be an integer between 0 and 8.')
    if preset_dict['transposition'] not in range(0,25):
        raise ValueError('The transposition must be an integer between 0 and 24.')
    if preset_dict['arpeggio']['enable'] not in [0, 1]:
        raise ValueError('The arpeggio enable must be 0 or 1.')
    if preset_dict['arpeggio']['mode'] not in range(0,6):
        raise ValueError('The arpeggio mode must be an integer between 0 and 5.')
    if preset_dict['arpeggio']['time_division'] not in range(0,8):
        raise ValueError('The arpeggio time_division must be an integer between 0 and 7.')
    if preset_dict['arpeggio']['clock'] not in [0, 1]:
        raise ValueError('The arpeggio clock must be 0 or 1.')
    if preset_dict['arpeggio']['latch'] not in [0, 1]:
        raise ValueError('The arpeggio latch must be 0 or 1.')
    if preset_dict['arpeggio']['tempo_taps'] not in range(2,5):
        raise ValueError('The arpeggio tempo_taps must be an integer between 2 and 4.')
    if preset_dict['arpeggio']['tempo_bpm'] not in range(30,241):
        raise ValueError('The arpeggio tempo_bpm must be an integer between 30 and 240.')
    if preset_dict['arpeggio']['octave'] not in range(0,4):
        raise ValueError('The arpeggio octave must be an integer between 0 and 3.')
    for pad in (preset_dict['pad_bank_1'] + preset_dict['pad_bank_2']):
        if pad['note'] not in range(0,256) or pad['pc'] not in range(0,256) or pad['cc'] not in range(0,256):
            raise ValueError('The pad note, pc and cc values must be integers between 0 and 255.')
        if pad['type'] not in [0, 1]:
            raise ValueError('The pad type must be 0 or 1.')
    for knob in preset_dict['knobs']:
        if knob['cc'] not in range(0,256):
            raise ValueError('The knob cc must be integers between 0 and 255.')
        if knob['low']>knob['high'] or knob['low'] not in range(0,128) or knob['high'] not in range(0,128):
            raise ValueError('The knob low and high values must be integers between 0 and 127 and low must be smaller than high.')
    return preset_dict

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        prog='miniflasher',
        description='Can read or write JSON configuration files from/to the Akai MPK Mini 1. Gen',
        epilog='')

    parser.add_argument('read_write', help="'r' or 'w' for reading or writing the file respectively.")
    parser.add_argument('preset_number', help='Integer from 1 to 4 determining the preset slot to be read or written.')
    parser.add_argument('filepath', help='The relative path to the file to be read from or written to.')

    args = parser.parse_args()
    valid_args = ValidArgs(args.read_write, args.preset_number, args.filepath)

    io = init_io()

    match valid_args.read_write:
        case ReadWrite.READ:
            preset_bytes = read_preset_bytes(io, valid_args.preset_no)
            preset_dict = to_dict_struct(preset_bytes)
            store_preset_json(preset_dict, valid_args)
        case ReadWrite.WRITE:
            preset_dict = load_preset_json(valid_args)
            preset_bytes = to_byte_struct(preset_dict)
            write_preset_bytes(io, valid_args.preset_no, preset_bytes)
