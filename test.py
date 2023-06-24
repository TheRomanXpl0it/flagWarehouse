

END				= "\033[0m"

BLACK			= "\033[30m"
GREY			= "\033[90m"
RED				= "\033[31m"
GREEN			= "\033[32m"
YELLOW			= "\033[33m"
BLUE			= "\033[34m"
PURPLE			= "\033[35m"
CYAN			= "\033[36m"

HIGH_RED		= "\033[91m"
HIGH_GREEN		= "\033[92m"
HIGH_YELLOW		= "\033[93m"
HIGH_BLUE		= "\033[94m"
HIGH_PURPLE		= "\033[95m"
HIGH_CYAN		= "\033[96m"


colors = [
	BLACK,
	GREY,
	PURPLE,
	BLUE,
	CYAN,
	GREEN,
	YELLOW,
	RED,
	HIGH_PURPLE,
	HIGH_BLUE,
	HIGH_CYAN,
	HIGH_GREEN,
	HIGH_YELLOW,
	HIGH_RED,
]


for color in colors:
    print(f"{color}test string with 12 numbers{END}")

print()

flags = [0] *20
invalid = 1
old = 1
nop = 1
accepted = 1
yours = 1

msg = f'Submitted {GREEN}{len(flags)}{END} flags: {GREEN}{accepted} Accepted{END}'
if old:
	msg += f' {CYAN}{old} Old{END}'
if nop:
	msg += f' {HIGH_PURPLE}{nop} NOP{END}'
if yours:
	msg += f' {HIGH_YELLOW}{yours} Yours{END}'
if invalid:
	msg += f' {RED}{invalid} Invalid{END}'
print(msg)