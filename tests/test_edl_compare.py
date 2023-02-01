from posttools import edl
import sys

if __name__ == "__main__":

	if len(sys.argv) < 3:
		sys.exit(f"Usage: {__file__} list1.edl list2.edl")
	
	try:
		with open(sys.argv[1]) as edl1:
			edl_source = edl.Edl.from_file(edl1)
	
		with open(sys.argv[2]) as edl2:
			edl_comp = edl.Edl.from_file(edl2)
	
	except Exception as e:
		sys.exit(f"Trouble parsing EDL: {e}")
	
	count_good = 0
	count_bad  = 0
	
	print("")

	for event_src, event_comp in zip(edl_source.events, edl_comp.events):
		reel_src = event_src.reel.lower().rstrip(".mov")
		reel_comp = event_comp.reel.lower().rstrip(".mov")

		if event_src.tc_record.start != event_comp.tc_record.start:
			print(f"Timecode fell off at {event_src.tc_record.start} / {reel_src} vs {event_comp.tc_record.start} / {reel_comp}")
			count_bad += 1
		elif reel_src != reel_comp:
			count_bad += 1
			print(f"[{event_src.tc_record.start}] {reel_src}  vs  {reel_comp}")
		else:
			count_good += 1
	
	print("\n---")
	print(f"{count_good} were good; {count_bad} were weird.")