#!/usr/bin/env python

import argparse

class EmuMachine:
	def __init__(self):
		self.cpu = self.CPU()
		self.ram = self.RAM()
		self.serial = self.Serial()

	class CPU:
		def __init__(self):
			self.A = 0
			self.PC = 0x100

		def set_pc(self, val):
			self.PC = (val & 0xfff)
			return

		def get_pc(self):
			return self.PC & 0xfff

		def advance_pc(self):
			self.set_pc(self.get_pc() + 2)

		def set_a(self, val):
			self.A = (val & 0xff)
			return

		def get_a(self):
			return self.A & 0xff

	class RAM:
		def __init__(self):
			self.memory = [0] * 0x1000
			"""acl could be implemented as a bitmask
			or as a dict, together with self.memory"""
			self.acl = [1] * len(self.memory)
			return

		def get_byte(self, addr):
			return self.memory[addr]

		def set_byte(self, addr, val):
			if self.acl[addr & 0xfff]:
				self.memory[addr] = val & 0xff
			return

		def set_writable(self, addr, flag):
			self.acl[addr & 0xfff] = flag
			return

	class Serial:
		def __init__(self):
			pass

		def write(self, b):
			f = open("serial", "ab")
			f.write(bytes([b]))
			f.close()
			return

	def load_rom(self, fname):
		f = open(fname, "rb")
		buf = f.read()
		f.close()
		self.ram.memory[0x100:0x100 + len(buf)] = list(buf)
		return True

	def decode_insn(self, insn):
		opc = insn >> 8

		# arithmetic
		if opc == 0x00:
			imm = insn & 0xff
			disasm = "add\tA, %xh" % imm
		elif opc == 0x01:
			imm = insn & 0xff
			disasm = "mov\tA, %xh" % imm
		elif opc == 0x02:
			imm = insn & 0xff
			disasm = "xor\tA, %xh" % imm
		elif opc == 0x03:
			imm = insn & 0xff
			disasm = "or\tA, %xh" % imm		
		elif opc == 0x04:
			imm = insn & 0xff
			disasm = "and\tA, %xh" % imm
		elif opc & 0xf0 == 0x80:
			imm = insn & 0xfff
			disasm = "stm\tA, [%xh]" % imm
		elif opc & 0xf0 == 0xd0:
			imm = insn & 0xfff
			disasm = "ldmxor\tA, [%xh]" % imm
		elif opc & 0xf0 == 0xf0:
			imm = insn & 0xfff
			disasm = "ldm\tA, [%xh]" % imm

		# i/o
		elif insn == 0x1337:
			disasm = "serout\tA"

		# cf
		elif opc & 0xf0 == 0x20:
			imm = insn & 0xfff
			disasm = "b\t%xh" % imm
		elif opc & 0xf0 == 0x30:
			imm = insn & 0xfff
			disasm = "bz\t%xh" % imm
		elif opc & 0xf0 == 0x40:
			imm = insn & 0xfff
			disasm = "bo\t%xh" % imm
		elif opc & 0xf0 == 0x50:
			imm = insn & 0xfff
			disasm = "bmax\t%xh" % imm
		elif opc == 0x60:
			imm = insn & 0xff
			disasm = "cmps\tA, %xh" % imm
		elif opc & 0xf0 == 0x70:
			imm = insn & 0xfff
			disasm = "cmps\tA, [%xh]" % imm
		elif insn == 0xbeef:
			disasm = "reset"

		# security
		elif opc & 0xf0 == 0x90:
			imm = insn & 0xfff
			disasm = "block\t%xh" % imm
		elif opc & 0xf0 == 0xa0:
			imm = insn & 0xfff
			disasm = "unblock\t%xh" % imm
		elif opc & 0xf0 == 0xc0:
			imm = insn & 0xfff
			disasm = "frobn\t[%xh]" % imm

		# misc
		elif insn == 0xeeee:
			disasm = "nop"

		else:
			disasm = "dec\tA"
		return "%03xh: %02x %02x\t%s" % (self.cpu.PC, (insn & 0xff00) >> 8, insn & 0xff, disasm)

	def emulate_insn(self, insn):
		opc = insn >> 8

		# arithmetic
		if opc == 0x00:
			self.cpu.set_a(self.cpu.get_a() + (insn & 0xff))
			self.cpu.advance_pc()
		elif opc == 0x01:
			self.cpu.set_a(insn & 0xff)
			self.cpu.advance_pc()
		elif opc == 0x02:
			self.cpu.set_a(self.cpu.get_a() ^ (insn & 0xff))
			self.cpu.advance_pc()
		elif opc == 0x03:
			self.cpu.set_a(self.cpu.get_a() | (insn & 0xff))
			self.cpu.advance_pc()
		elif opc == 0x04:
			self.cpu.set_a(self.cpu.get_a() & (insn & 0xff))
			self.cpu.advance_pc()
		elif opc & 0xf0 == 0x80:
			self.cpu.set_a(self.ram.get_byte(insn & 0xfff))
			self.cpu.advance_pc()
		elif opc & 0xf0 == 0xd0:
			self.ram.set_byte(insn & 0xfff, self.ram.get_byte(insn & 0xfff) ^ self.cpu.get_a())
			self.cpu.advance_pc()
		elif opc & 0xf0 == 0xf0:
			self.ram.set_byte(insn & 0xfff, self.cpu.get_a())
			self.cpu.advance_pc()	

		# i/o
		elif insn == 0x1337:
			self.serial.write(self.cpu.get_a())
			self.cpu.advance_pc()

		# cf
		elif opc & 0xf0 == 0x20:
			self.cpu.set_pc(insn & 0xfff)
		elif opc & 0xf0 == 0x30:
			if self.cpu.get_a() == 0:
				self.cpu.set_pc(insn & 0xfff)
			else:
				self.cpu.advance_pc()
		elif opc & 0xf0 == 0x40:
			if self.cpu.get_a() == 1:
				self.cpu.set_pc(insn & 0xfff)
			else:
				self.cpu.advance_pc()
		elif opc & 0xf0 == 0x50:
			if self.cpu.get_a() == 0xff:
				self.cpu.set_pc(insn & 0xfff)
			else:
				self.cpu.advance_pc()
		elif opc == 0x60:
			if self.cpu.get_a() == insn & 0xff:
				self.cpu.set_a(0)
			elif self.cpu.get_a() < insn & 0xff:
				self.cpu.set_a(1)
			elif self.cpu.get_a() > insn & 0xff:
				self.cpu.set_a(0xff)
			self.cpu.advance_pc()
		elif opc & 0xf0 == 0x70:
			xx = self.ram.memory[insn & 0xfff]
			if self.cpu.get_a() == xx:
				self.cpu.set_a(0)
			elif self.cpu.get_a() < xx:
				self.cpu.set_a(1)
			elif self.cpu.get_a() > xx:
				self.cpu.set_a(0xff)
			self.cpu.advance_pc()
		elif insn == 0xbeef:
			self.cpu.set_pc (0x100)
			self.cpu.set_a(0x42)

		# security
		elif opc & 0xf0 == 0x90:
			self.ram.set_writable(insn & 0xfff, False)
			self.cpu.advance_pc()
		elif opc & 0xf0 == 0xa0:
			self.ram.set_writable(insn & 0xfff, True)
			self.cpu.advance_pc()
		elif opc & 0xf0 == 0xc0:
			self.ram.set_byte(insn & 0xfff, self.ram.get_byte(insn & 0xfff) ^ 0x42)
			self.cpu.advance_pc()

		# misc
		elif insn == 0xeeee:
			self.cpu.advance_pc()

		else:
			self.cpu.set_a((self.cpu.get_a() - 1))
			self.cpu.advance_pc()

		return

	def fetch_insn(self):
		insn = (self.ram.get_byte(self.cpu.get_pc()) << 8) | self.ram.get_byte(self.cpu.get_pc() + 1)
		return insn

	def run(self, debug=False):
		suspended = debug
		while True:
			if not suspended:
				insn = self.fetch_insn()
				if not debug:
					print(self.decode_insn(insn))
				self.emulate_insn(insn)
			else:
				inp = input("> ").lower()
				if inp == "h":
					print("[h]elp, [d]isasm, [r]regs, [s]tep, [c]ont, [q]uit")
				elif inp == "q":
					break
				elif inp == "r":
					print("PC:\t%3xh\nA:\t%02xh" % (self.cpu.get_pc(), self.cpu.get_a()))
				elif inp == "d":
					insn = self.fetch_insn()
					print(self.decode_insn(insn))
				elif inp == "s":
					insn = self.fetch_insn()
					self.emulate_insn(insn)
					insn = self.fetch_insn()
					print(self.decode_insn(insn))
				elif inp == "c":
					suspended = False
				else:
					print("Unsupported command. Type 'h' for help.")
		return

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", help="enable debugger", action="store_true")
	args = parser.parse_args()

	em = EmuMachine()
	em.load_rom("rom")
	em.run(debug=args.debug)
