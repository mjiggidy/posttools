import sys
from posttools.edl import Edl

def main():

	if len(sys.argv) > 1:
		for path_edl in sys.argv[1:]:
			print(path_edl,":")
			with open(path_edl) as file_edl:
				edl = Edl.from_file(file_edl)
				print(edl)
				print("Tracks:", edl.tracks)
	else:
		print(Edl())


if __name__ == "__main__":

	main()