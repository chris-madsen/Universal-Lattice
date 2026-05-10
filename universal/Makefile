.PHONY: universal-build universal-doc universal-all clean

universal-build:
	python3 build_universal_from_2T_plus_16.py

universal-doc:
	@echo "Documentation is source-controlled in universal_rune_lattice_from_2T_plus_16.md"
	@echo "Generated report: out/summary.md"

universal-all: universal-build universal-doc

clean:
	rm -f out/*.json out/*.md out/*.png
