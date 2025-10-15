@echo -off

# Check if the number of arguments is correct
if "%1" == "" then
    echo "Usage: script.nsh <N>"
    exit 1
endif

set N=%1  # Set N from the command line argument

for %i in (1..%N) do (
    echo Executing iteration %i
    YourCommand
)