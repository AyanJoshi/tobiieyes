import haptic
import random
import glob
import time
import os

DELAY = 0.1

patterns, interface, pdata = haptic.main()

mapping = {
	'happy': 1,
	'sad': 2,
	'surprise': 13,
	'anger': 5,
	'fear': 6,
	'disgust': 15,
	'neutral': 15,
}

durations = len(pdata["durations"])

def run_pattern(i):
	patterns[i * durations]()


def main():
	files = glob.glob("../*.txt")

	if len(files) == 0:
		return None

	files.sort()
	fpath = files.pop()
	with open(fpath) as txtfile:
		txt = txtfile.read()
		print txt
		for m in mapping:
			if m in txt:
				print m
				run_pattern(mapping[m])
				break

	os.remove(fpath)

	for f in files:
		os.remove(f)

if __name__ == "__main__":
	while True:
		main()
		time.sleep(DELAY)
