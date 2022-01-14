from posttools.timecode import Timecode, TimecodeRange

tc_range = TimecodeRange(
	start= Timecode("00:00:00;00", 30, Timecode.Mode.DF),
	end  = Timecode("0:15:00;00", 30, Timecode.Mode.DF)
)

#checker = lambda x: x._df_offset()
checker = lambda x: x._df_to_ndf_offset()

for tc in tc_range: print(str(tc), '\t', Timecode(str(tc), 30, Timecode.Mode.DF), '\t', tc - Timecode(str(tc), 30, Timecode.Mode.DF))

"""
offset = None
for tc in tc_range:
	if checker(tc) != offset:
		offset = checker(tc)
		print(tc-1)
		formatted = str(tc)
		print(formatted, '\t', offset)
		print(tc+1)
		print("")
"""