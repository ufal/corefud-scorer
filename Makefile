SHELL=/bin/bash

convert_tests:
	mkdir -p corefud_tests
	for f in tests/*.{response,key}; do\
		file=`basename $$f`;\
		python convert_test_files.py < $$f > corefud_tests/$$file;\
	done

corefud_test :
	pytest corefud-unittests.py
