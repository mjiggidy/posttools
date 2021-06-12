from posttools.timecode import Timecode, TimecodeRange

rate = 30
mode = Timecode.Mode.DF

tc_start = Timecode(0, rate, mode)
tc_duration = Timecode(rate * 60 * 1000, rate, mode)
tc_range = TimecodeRange(start=tc_start, duration=tc_duration)


#for tc in tc_range:
#	print(tc, tc._df_offset)
#exit
old_offset = -1
for tc in tc_range:
	offset = tc._df_offset
	if offset != old_offset:
		old_offset = offset
		print(tc, tc._df_offset)