import sys, typing
from posttools.edl import Edl, Track, Event, StandardFormStatement

def show_stats(edl:Edl):
	"""Print dem stats"""
	#print(f"{edl.title} contains {len(edl.events)} events across {len(edl.tracks)} tracks")
	#print(len(edl.events))
	
	print(f"EDL Title: {edl.title}")
	print(f"EDL FCM: {edl.fcm.value}")
	print("---")
	print(f"Contains {len(edl.tracks)} tracks ({len([t for t in edl.tracks if t.type is Track.Type.VIDEO])} video; {len([t for t in edl.tracks if t.type is Track.Type.AUDIO])} audio)")
	print(f"Contains {len(edl.events)} events")
	print("---")
	print(f"Contains {len(edl.sources)} unique sources:")

	for source in sorted(edl.sources, key=lambda x: x._NAME):
		print(source)

	#edl_with_black(edl.events)

def edl_with_black(events:typing.Iterable[Event]):
	"""Create a new EDL with just black"""

	edl = Edl(title="Black Stuff XXL")
	for event in events:
		if event.is_filler:
			edl.events.append(event)
	
	print(edl)

	#return
	#for idx, event in enumerate(edl.events):
	#	print(idx+1, event.reel)

def main():

	for path_edl in sys.argv[1:]:
		print(path_edl,":")
		with open(path_edl) as file_edl:
			show_stats(Edl.from_file(file_edl))


if __name__ == "__main__":

	main()