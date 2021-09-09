import numpy as np

class Assembler():

    def __init__(self):
        self.instruction_translator = {
            "NOP": "0000",
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
            "NOP": False,
            "LDA": False,
            "ADD": False,
            "SUB": False,
            "LDI": True,
            "STA": False,
            "JMP": True,
            "JEQ": True,
            "CEQ": False,
            "JSR": True,
            "RET": False
        } 

        self.vhdl = '--         OPCode     Imediate\n'
        ## tmp(0)  := "0100" & "0" & "00000100";


    def readFile(self, filename):
        try:
            with open(filename, "r") as f:
                self.data = f.read().split("\n")
        except Exception as e:
            print(f"Error reading file!\n {e}")

    def processData(self):
        
        for line, instruction_line in enumerate(self.data):
            if not instruction_line: # Vazio
                continue # avança
            instruction_components = instruction_line.split(" ")
            instruction_current = instruction_components[0]
            if instruction_current in self.instruction_translator.keys():
                if self.instruction_args[instruction_current]:
                    if len(instruction_components) < 2:
                        print(f"Instruction on line {line} is invalid! {instruction_current} requires an argument!")
                    instruction_argument = int(instruction_components[1])
                else:
                    instruction_argument = 0
                translated_instruction = self.instruction_translator[instruction_current]
                if instruction_argument != 0:
                    self.vhdl += f'tmp({line})  := "{translated_instruction}" & "{instruction_argument:09b}"; -- {instruction_current} {instruction_argument}\n'
                else:
                    self.vhdl += f'tmp({line})  := "{translated_instruction}" & "{instruction_argument:09b}"; -- {instruction_current}\n'

    def writeVHDL(self, filename):
        try:
            with open(filename, "w") as f:
                f.write(self.vhdl)
        except Exception as e:
            print(f"Error writing file!\n {e}")


if __name__ == "__main__":
    assembler = Assembler()
    assembler.readFile("sampleAssembly.txt")
    assembler.processData()
    assembler.writeVHDL("out.txt")



