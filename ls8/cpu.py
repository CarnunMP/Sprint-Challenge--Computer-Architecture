"""CPU functionality."""

import sys

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0 # program counter
        self.fl = 0 # flags register

        # stack pointer:
        self.reg[7] = 0xF4 # F4 is ram address of 'Key Pressed'; stack ranges from F3 _downward_

    def ram_read(self, decimal_address):
        return self.ram[decimal_address]

    def ram_write(self, value, decimal_address):
        self.ram[decimal_address] = value

    def load(self, relative_file_path):
        """Load a program into memory."""

        address = self.pc

        # For now, we've just hardcoded a program:
        # program = [
        #     # From print8.ls8
        #     0b10000010, # LDI R0,8
        #     0b00000000,
        #     0b00001000,
        #     0b01000111, # PRN R0
        #     0b00000000,
        #     0b00000001, # HLT
        # ]

        program = []
        
        with open(relative_file_path) as f:
            for line in f:
                if line[0] == "0" or line[0] == "1":
                    program.append(int(line[:8], 2))

        for instruction in program:
            self.ram[address] = instruction
            address += 1


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "CMP":
            # FL holds bits of the form '00000LGE', where L = '<', G = '>', and E = '='
            L = '0'
            G = '0'
            E = '0'

            if self.reg[reg_a] < self.reg[reg_b]:
                L = '1'
            elif self.reg[reg_a] > self.reg[reg_b]:
                G = '1'

            if self.reg[reg_a] == self.reg[reg_b]:
                E = '1'

            self.fl = int(f'00000{L}{G}{E}', 2)
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        ops = {
            # ALU ops
            'ADD': 0b10100000,
            'SUB': 0b10100001,
            'MUL': 0b10100010,
            'CMP': 0b10100111,

            # PC mutators
            'CALL': 0b01010000,
            'RET': 0b00010001,
            'JMP': 0b01010100,

            # Other
            'HLT': 0b00000001,
            'LDI': 0b10000010,
            'PUSH': 0b01000101,
            'POP': 0b01000110,
            'PRN': 0b01000111,
        }
        
        # ALU ops
        def ADD(reg_a, reg_b):
            self.alu('ADD', reg_a, reg_b)

        def SUB(reg_a, reg_b):
            self.alu('SUB', reg_a, reg_b)

        def MUL(reg_a, reg_b):
            self.alu('MUL', reg_a, reg_b)

        def CMP(reg_a, reg_b):
            self.alu('CMP', reg_a, reg_b)


        # PC mutators
        def CALL(operand_a):
            self.reg[6] = self.pc + 2 # Interrupt Status; +2 because CALL takes one operand
            PUSH(6)
            self.pc = self.reg[operand_a]

        def RET():
            POP(0)
            self.pc = self.reg[0]

        def JMP(operand_a):
            self.pc = self.reg[operand_a]


        # Other
        def HLT():
            sys.exit(0)

        def LDI(operand_a, operand_b):
            self.reg[operand_a] = operand_b

        def PUSH(operand_a): # here, operand_a is a reg address
            self.reg[7] -= 1
            self.ram[self.reg[7]] = self.reg[operand_a]

        def POP(operand_a): # here too!
            if self.reg[7] < 0xF4:
                self.reg[operand_a] = self.ram[self.reg[7]]
                self.reg[7] += 1
            else:
                print('WARNING: cannot POP an empty stack!')

        def PRN(operand_a):
            print(self.reg[operand_a])


        branchtable = {
            # ALU ops
            ops['ADD']: ADD,
            ops['SUB']: SUB,
            ops['MUL']: MUL,
            ops['CMP']: CMP,

            # PC mutators
            ops['CALL']: CALL,
            ops['RET']: RET,
            ops['JMP']: JMP,

            # Other
            ops['HLT']: HLT,
            ops['LDI']: LDI,
            ops['PUSH']: PUSH,
            ops['POP']: POP,
            ops['PRN']: PRN
        }

        

        while True:
            IR = self.ram[self.pc] # Instruction Register

            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            number_of_operands = IR >> 6

            if number_of_operands == 0:
                branchtable[IR]()
            elif number_of_operands == 1:
                branchtable[IR](operand_a)
            elif number_of_operands == 2:
                branchtable[IR](operand_a, operand_b)

            instruction_sets_the_pc = (IR >> 4) & 1 == 1
            if not instruction_sets_the_pc:
                self.pc += (number_of_operands + 1) # ensures pc is incremented appropriately

