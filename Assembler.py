import numpy as np
import tkinter.filedialog as tkfd
from tkinter import Tk

class Assembler():

    def __init__(self):

        """
        Manual:
       
        NÃO USAR VÍRGULAS, SEPARADOR = ' '
        
        REGISTRADORES NOMEADOS DE 0 a 7 (8) OU ALTERNATIVAMENTE
        RA a RD + RX,RY PARA REGISTRADORES DE USO GERAL, RI PARA CONTADORES E RR PARA RETORNOS DE FUNÇÃO 
        
        DEFINIÇÕES DE FUNÇÃO SEMPRE NO COMEÇO DO ARQUIVO
        
        QUANDO INDICANDO ENDEREÇOS PARA COMANDOS JUMP, É POSSÍVEL INDICAR SALTOS RELATIVOS, COMO
        JMP +5 INDICA, SALTE CINCO POSIÇÕES ADIANTE, OU JEQ -5 INDICA, CASO CEQ, SALTE 5 POSIÇÕES PARA TRÁS

        NOP
        DEF FUNC_NAME
        LDA REG MEM_ADDR
        ADD REG MEM_ADDR
        SUB REG MEM_ADDR
        LDI REG VALUE (0-255)
        STA REG MEM_ADDR
        JMP MEM_ADDR
        JEQ MEM_ADDR
        CEQ REG MEM_ADDR
        JSR MEM_ADDR/FUNC_NAME
        RET
        """


        self.instruction_translator = {
            "LDA": "0001",
            "ADD": "0010",
            "SUB": "0011",
            "LDI": "0100",
            "STA": "0101",
            "JMP": "0110",
            "JEQ": "0111",
            "CEQ": "1000",
            "JSR": "1001",
            "RET": "1010"
        } 

        self.instruction_args = {
            "LDA": 2,
            "ADD": 2,
            "SUB": 2,
            "LDI": 2,
            "STA": 2,
            "JMP": 1,
            "JEQ": 1,
            "CEQ": 2,
            "JSR": 1,
            "RET": 0
        }

        self.symbol_table = {
            "LED0TO7":256,
            "LED8": 257,
            "LED9": 258,
            "HEX0":288,
            "HEX1":289,
            "HEX2":290,
            "HEX3":291,  
            "HEX4":292,
            "HEX5":293,
            "SW7TO0":320,
            "SW8":321,
            "SW9":322,
            "KEY0":352,
            "KEY1":353,
            "KEY2":354,
            "KEY3":355,
            "RST":356,
            "FPGA_RESET":356,
            "CLR1":510,
            "CLR0":511,
            "RA":0,
            "RB":1,
            "RC":2,
            "RD":3,
            "RX":4,
            "RY":5,
            "RI":6,
            "RR":7           
        } 

        self.sr_map={}

        self.vhdl = '''
library IEEE;
use IEEE.std_logic_1164.all;
use ieee.numeric_std.all;

entity memoriaROM is
generic (
        dataWidth: natural := 8;
        addrWidth: natural := 4
    );
port (
        Endereco : in std_logic_vector (addrWidth-1 DOWNTO 0);
        Dado : out std_logic_vector (dataWidth-1 DOWNTO 0)
    );
end entity;

architecture assincrona of memoriaROM is

type blocoMemoria is array(0 TO 2**addrWidth - 1) of std_logic_vector(dataWidth-1 DOWNTO 0);

function initMemory
        return blocoMemoria is variable tmp : blocoMemoria := (others => (others => '0'));
begin 
\n-- Traduzido automaticament via python\n'''
        self.func_vhdl = '\n'
        self.lineCounter = 0
        self.finalMemoryAddress = 511

    def readFile(self):
        Tk().withdraw()
        filename = ""
        filename = tkfd.askopenfilename(title='Indicate assembly file')
        print(f"Chosen file: {filename}")
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.data = f.read()
                for k,v in self.symbol_table.items():
                    self.data = self.data.replace(k, str(v))
                self.data = self.data.split("\n")
        except Exception as e:
            print(f"Error reading file!\n {e}")

    def _defineSubroutine(self, instruction_line, line):
        SR_name = instruction_line.split(" ")[1].upper()
        self.func_vhdl += f"-- DEF Subrotina {SR_name.upper()}\n"
        line_index = line
        next = self.data[line_index]
        size_counter = 1
        if SR_name.upper() in self.sr_map.keys():
            print("Function names must be unique")
            return 0
        while next.strip() != "RET":
            line_index += 1
            next = self.data[line_index]
            if next == "":
                continue
            size_counter += 1
        self.finalMemoryAddress -= size_counter
        self.sr_map[SR_name.upper()] = self.finalMemoryAddress + 2
        comment_offset = 0
        for i in range(1,size_counter):
            instruction_components = self.data[line+i].split(" ")
            instruction_current = instruction_components[0].upper()
            if instruction_current == "DEF":
                raise Exception("Sub-Subroutines not allowed! Either you forgot to RET or you tried using a DEF inside a Subroutine!")
            if instruction_current.startswith("--"):
                comment_offset += 1
                continue
            if instruction_current in self.instruction_translator.keys():
                arg_count = self.instruction_args[instruction_current]
                translated_instruction = self.instruction_translator[instruction_current]
                if arg_count != 0:
                    if len(instruction_components) < arg_count+1:
                        print(f"Instruction on line {line+i} is invalid! {instruction_current} requires an argument!")
                    instruction_argument_list = instruction_components[1:]
                    if arg_count == 1:
                        address = self._parseAddress(instruction_argument_list[0], self.finalMemoryAddress+i+1-comment_offset)
                        self.func_vhdl += f'tmp({self.finalMemoryAddress+i+1-comment_offset})\t\t:= "{translated_instruction}" & "{0:03b}" & "{address:09b}"; -- {self.data[line+i]}\n'
                    elif arg_count == 2:
                        reg = int(instruction_argument_list[0])
                        address = int(instruction_argument_list[1])
                        self.func_vhdl += f'tmp({self.finalMemoryAddress+i+1-comment_offset})\t\t:= "{translated_instruction}" & "{reg:03b}" & "{address:09b}"; -- {self.data[line+i]}\n'
                else:
                    self.func_vhdl += f'tmp({self.finalMemoryAddress+i+1-comment_offset})\t\t:= "{translated_instruction}" & "{0:03b}" & "{0:09b}"; -- {instruction_current}\n'
        self.func_vhdl+="\n"
        return size_counter

    def _parseAddress(self, address_str, currentLine):
        if address_str.startswith("+"):
            out = int(address_str[1:])+currentLine
        elif address_str.startswith("-"):
            out = currentLine-int(address_str[1:])
        else:
            out = int(address_str)
        return out

    def processData(self):
        skip_lines = 0
        for line, instruction_line in enumerate(self.data):
            if skip_lines > 0:
                skip_lines -= 1
                continue
            if instruction_line == "": # Vazio
                continue # avança
            # if instruction_line.startswith("--"):
            #     self.func_vhdl += instruction_line+"\n"
            instruction_components = instruction_line.split(" ")
            instruction_current = instruction_components[0].upper()
            
            if instruction_current.upper() == "NOP":
                self.lineCounter += 1
                continue

            if instruction_current.upper() == "DEF":
                skip_lines = self._defineSubroutine(instruction_line, line)               
                continue
            
            for k,v in self.sr_map.items():
                instruction_line = instruction_line.upper().replace(k, str(v))

            instruction_components = instruction_line.split(" ")
            instruction_current = instruction_components[0].upper()

            if instruction_current in self.instruction_translator.keys():
                arg_count = self.instruction_args[instruction_current]
                translated_instruction = self.instruction_translator[instruction_current]
                if arg_count != 0:
                    if len(instruction_components) < arg_count+1:
                        print(f"Instruction on line {line} is invalid! {instruction_current} requires an argument!")
                    instruction_argument_list = instruction_components[1:]
                    if arg_count == 1:
                        address = self._parseAddress(instruction_argument_list[0], self.lineCounter)
                        self.vhdl += f'tmp({self.lineCounter})\t\t:= "{translated_instruction}" & "{0:03b}" & "{address:09b}"; -- {instruction_line}\n'
                        self.lineCounter += 1
                    elif arg_count == 2:
                        reg = int(instruction_argument_list[0])
                        address = int(instruction_argument_list[1])
                        self.vhdl += f'tmp({self.lineCounter})\t\t:= "{translated_instruction}" & "{reg:03b}" & "{address:09b}"; -- {instruction_line}\n'
                        self.lineCounter += 1
                else:
                    self.vhdl += f'tmp({self.lineCounter})\t\t:= "{translated_instruction}" & "{0:03b}" & "{0:09b}"; -- {instruction_current}\n'
                    self.lineCounter += 1

    def writeVHDL(self, filename):
        self.vhdl += f"\n-- END OF MAIN --\n-- DEFINED SUBROUTINES BELOW --\n"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.vhdl + self.func_vhdl + '''
return tmp;
    end initMemory;

    signal memROM : blocoMemoria := initMemory;

begin
    Dado <= memROM (to_integer(unsigned(Endereco)));
end architecture;
''')
        except Exception as e:
            print(f"Error writing file!\n {e}")


if __name__ == "__main__":
    print("Starting!")
    assembler = Assembler()
    assembler.readFile()
    assembler.processData()
    assembler.writeVHDL("out.txt")
    print("Done!")


