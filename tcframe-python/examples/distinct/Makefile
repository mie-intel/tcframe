CXX     = g++
CXXFLAGS = -std=c++17 -O2

all: solution_ac solution_tle solution_mle

solution_ac:  solution_ac.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

solution_tle: solution_tle.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

solution_mle: solution_mle.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f solution_ac solution_tle solution_mle

.PHONY: all clean
