import os
import sys
import subprocess
import time


def ensure_output_directory(output_directory):
    """
    Ensures the output directory exists. If not, creates it.
    :param output_directory: Path to the output directory.
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)


def convert_xsb_to_smv(xsb_content):
    """
    Converts an XSB board format into an SMV model for NuXmv.
    :param xsb_content: The XSB board content as a string.
    :return: The converted SMV model as a string.
    """
    smv_content = "MODULE main\nVAR\n"
    rows = xsb_content.split('\n')
    height = len(rows)
    width = max(len(row) for row in rows)

    # Define the board and shift variables
    smv_content += (f"    board : array 0..{height - 1} of array 0..{width - 1} of {{\"wk\", \"wk_on_goal\", \"box\", "
                    f"\"box_on_goal\", \"wall\", \"goal\", \"floor\"}};\n")
    smv_content += "    shift_move : {\"l\",\"u\",\"r\",\"d\",0};\n"
    smv_content += "    shift_push : {\"L\",\"U\",\"R\",\"D\",0};\n"

    smv_content += "\nASSIGN\n"
    # Initialize the board
    for i, row in enumerate(rows):
        for j, char in enumerate(row):
            if char == '@':  # Warehouse keeper
                smv_content += f"    init(board[{i}][{j}]) := \"wk\";\n"
            elif char == '+':  # Warehouse keeper on goal
                smv_content += f"    init(board[{i}][{j}]) := \"wk_on_goal\";\n"
            elif char == '$':  # Box
                smv_content += f"    init(board[{i}][{j}]) := \"box\";\n"
            elif char == '*':  # Box on goal
                smv_content += f"    init(board[{i}][{j}]) := \"box_on_goal\";\n"
            elif char == '#':  # Wall
                smv_content += f"    init(board[{i}][{j}]) := \"wall\";\n"
            elif char == '.':  # Goal
                smv_content += f"    init(board[{i}][{j}]) := \"goal\";\n"
            elif char == '-':  # Floor
                smv_content += f"    init(board[{i}][{j}]) := \"floor\";\n"
            elif char not in '@+$*#.-':
                raise ValueError(f"Unexpected character '{char}' in board at position ({i}, {j})")

    smv_content += "    init(shift_move) := 0;\n"
    smv_content += "    init(shift_push) := 0;\n"

    smv_content += "\nDEFINE\n"
    # Define valid moves and pushes
    for i in range(height):
        for j in range(width):
            if rows[i][j] != '#':
                # Left move/push
                if j > 0 and rows[i][j - 1] != '#':
                    smv_content += (f"    Left_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & (board[{i}][{j - 1}] = "
                                    f"\"floor\" | board[{i}][{j - 1}] = \"goal\");\n")
                    if j > 1 and rows[i][j - 2] != '#':
                        smv_content += (
                            f"    Left_push_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & board[{i}][{j - 1}] = "
                            f"\"box\" & (board[{i}][{j - 2}] = \"floor\" | board[{i}][{j - 2}] = \"goal\");\n")
                # Up move/push
                if i > 0 and rows[i - 1][j] != '#':
                    smv_content += (
                        f"    Up_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & (board[{i - 1}][{j}] = \"floor"
                        f"\" | board[{i - 1}][{j}] = \"goal\");\n")
                    if i > 1 and rows[i - 2][j] != '#':
                        smv_content += (
                            f"    Up_push_valid[{i}][{j}] :=(board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & board[{i - 1}][{j}] = "
                            f"\"box\" & (board[{i - 2}][{j}] = \"floor\" | board[{i - 2}][{j}] = \"goal\");\n")
                # Right move/push
                if j < width - 1 and rows[i][j + 1] != '#':
                    smv_content += (
                        f"    Right_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & (board[{i}][{j + 1}] = "
                        f"\"floor\" | board[{i}][{j + 1}] = \"goal\");\n")
                    if j < width - 2 and rows[i][j + 2] != '#':
                        smv_content += (
                            f"    Right_push_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & board[{i}][{j + 1}] = "
                            f"\"box\" & (board[{i}][{j + 2}] = \"floor\" | board[{i}][{j + 2}] = \"goal\");\n")
                # Down move/push
                if i < height - 1 and rows[i + 1][j] != '#':
                    smv_content += (f"    Down_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & (board[{i + 1}][{j}] = "
                                    f"\"floor\" | board[{i + 1}][{j}] = \"goal\");\n")
                    if i < height - 2 and rows[i + 2][j] != '#':
                        smv_content += (
                            f"    Down_push_valid[{i}][{j}] := (board[{i}][{j}] = \"wk\"|board[{i}][{j}] = \"wk_on_goal\") & board[{i + 1}][{j}] = "
                            f"\"box\" & (board[{i + 2}][{j}] = \"floor\" | board[{i + 2}][{j}] = \"goal\");\n")



    # Define the winning condition
    target_conditions = [f"board[{i}][{j}] = \"box_on_goal\"" for i, row in enumerate(rows) for j, char in
                         enumerate(row) if char in '.+*']
    win_condition = " & ".join(target_conditions)

    smv_content += "\nASSIGN\n"
    smv_content += "    next(shift_move) := {\"l\",\"u\",\"r\",\"d\"};\n"

    smv_content += "    next(shift_push) := case\n"
    smv_content += "        next(shift_move) = \"l\" : \"L\";\n"
    smv_content += "        next(shift_move) = \"u\" : \"U\";\n"
    smv_content += "        next(shift_move) = \"r\" : \"R\";\n"
    smv_content += "        next(shift_move) = \"d\" : \"D\";\n"
    smv_content += "        TRUE : 0 ;\n"
    smv_content += "    esac;\n\n"

    # Update board cells based on moves and pushes
    for i in range(height):
        for j in range(width):
            smv_content += f"    next(board[{i}][{j}]) := case\n"
            if rows[i][j] != '#':
                # Handle warehouse keeper movement and box pushes
                # Left move/push
                if j > 0:
                    if rows[i][j - 1] != '#':
                        # Move left (without pushing a box)
                        smv_content += f"        Left_valid[{i}][{j}] & next(shift_move) = \"l\" : "
                        smv_content += f"case board[{i}][{j}] = \"wk_on_goal\" : \"goal\"; TRUE : \"floor\"; esac;\n"
                    if j < width - 2 and rows[i][j + 1] != '#':
                        smv_content += f"        Left_valid[{i}][{j + 1}] & next(shift_move) = \"l\" : "
                        smv_content += f"case board[{i}][{j}] = \"goal\" : \"wk_on_goal\"; TRUE : \"wk\"; esac;\n"
                        if j < width - 3 and rows[i][j + 2] != '#':
                            # Push left (with a box)
                            smv_content += f"        Left_push_valid[{i}][{j + 2}] & next(shift_push) = \"L\":"
                            smv_content += f"case board[{i}][{j}] = \"goal\" : \"box_on_goal\"; TRUE : \"box\"; esac;\n"
                # Up move/push
                if i > 0:
                    if rows[i - 1][j] != '#':
                        # Move up (without pushing a box)
                        smv_content += f"        Up_valid[{i}][{j}] & next(shift_move) = \"u\" : "
                        smv_content += f"case board[{i}][{j}] = \"wk_on_goal\" : \"goal\"; TRUE : \"floor\"; esac;\n"
                    if i < height - 2 and rows[i + 1][j] != '#':
                        smv_content += f"        Up_valid[{i + 1}][{j}] & next(shift_move) = \"u\" : "
                        smv_content += f"case board[{i}][{j}] = \"goal\" : \"wk_on_goal\"; TRUE : \"wk\"; esac;\n"
                        if i < height - 3 and rows[i + 2][j] != '#':
                            # Push up (with a box)
                            smv_content += f"        Up_push_valid[{i + 2}][{j}] & next(shift_push) = \"U\":"
                            smv_content += f"case board[{i}][{j}] = \"goal\" : \"box_on_goal\"; TRUE : \"box\"; esac;\n"
                # Right move/push
                if j < width - 1:
                    if rows[i][j + 1] != '#':
                        # Move right (without pushing a box)
                        smv_content += f"        Right_valid[{i}][{j}] & next(shift_move) = \"r\" : "
                        smv_content += f"case board[{i}][{j}] = \"wk_on_goal\" : \"goal\"; TRUE : \"floor\"; esac;\n"
                    if j > 1 and rows[i][j - 1] != '#':
                        smv_content += f"        Right_valid[{i}][{j - 1}] & next(shift_move) = \"r\" : "
                        smv_content += f"case board[{i}][{j}] = \"goal\" : \"wk_on_goal\"; TRUE : \"wk\"; esac;\n"
                        if j > 2 and rows[i][j - 2] != '#':
                            # Push right (with a box)
                            smv_content += f"        Right_push_valid[{i}][{j - 2}] & next(shift_push) = \"R\": "
                            smv_content += f"case board[{i}][{j}] = \"goal\" : \"box_on_goal\"; TRUE : \"box\"; esac;\n"
                # Down move/push
                    if i < height - 1:
                        # Move down (without pushing a box)
                        if rows[i + 1][j] != '#':
                            smv_content += f"        Down_valid[{i}][{j}] & next(shift_move) = \"d\" : "
                            smv_content += f"case board[{i}][{j}] = \"wk_on_goal\" : \"goal\"; TRUE : \"floor\"; esac;\n"
                        if i > 1 and rows[i - 1][j] != '#':
                            smv_content += f"        Down_valid[{i - 1}][{j}] & next(shift_move) = \"d\" : "
                            smv_content += f"case board[{i}][{j}] = \"goal\" : \"wk_on_goal\";  TRUE : \"wk\"; esac;\n"
                            # Push down (with a box)
                            if i > 2 and rows[i - 2][j] != '#':
                                smv_content += f"        Down_push_valid[{i - 2}][{j}] & next(shift_push) = \"D\":"
                                smv_content += f"case board[{i}][{j}] = \"goal\" : \"box_on_goal\"; TRUE : \"box\"; esac;\n"

            smv_content += f"        TRUE : board[{i}][{j}];\n"
            smv_content += f"    esac;\n\n"
    # if exist get the trace
    smv_content += f"CTLSPEC AG!({win_condition});\n"

    return smv_content


def validate_nuxmv_execution(output_file):
    """
    Validates whether NuXmv ran successfully by checking its output file.
    :param output_file: Path to the NuXmv output file.
    :return: True if successful, False otherwise.
    """
    try:
        with open(output_file, 'r') as f:
            content = f.read()
            if "TRUE" in content:  # Check if the result is TRUE
                return True
            elif "Error" in content or "usage" in content:
                return False
    except FileNotFoundError:
        return False
    return False


def run_nuxmv(model_filename, output_dir):
    """
    Runs NuXmv with the given SMV model file and saves the output.
    :param model_filename: Path to the SMV model file.
    :param output_dir: Directory to save the output files.
    :return: A dictionary containing the output filenames, success status, and runtime.
    """
    results = {}

    bdd_commands = """go
build_model
check_ltlspec
show_traces
"""
    sat_commands = """go_bmc
check_ltlspec_bmc -k 20
show_traces
quit
"""
    with open("nuxmv_bdd_commands.txt", "w") as f:
        f.write(bdd_commands)
    with open("nuxmv_sat_commands.txt", "w") as f:
        f.write(sat_commands)
    # Define output filenames
    bdd_output_file = os.path.join(output_dir, "nuxmv_bdd_output.txt")
    sat_output_file = os.path.join(output_dir, "nuxmv_sat_output.txt")

    # Run nuXmv with BDD engine (CTL model checking)
    print("Running nuXmv with BDD engine (CTL model checking)...")
    with open(bdd_output_file, "w") as f:
        bdd_start_time = time.time()
        nuxmv_process = subprocess.run(
            ["nuxmv", model_filename],  # Use CTL model checking
            input=bdd_commands,
            text=True,
            stdout=f,
            stderr=f
        )
    bdd_end_time = time.time()
    bdd_time = bdd_end_time - bdd_start_time

    # Validate BDD output
    results['bdd_success'] = validate_nuxmv_execution(bdd_output_file)

    # Run nuXmv with SAT engine (BMC for LTL)
    print("Running nuXmv with SAT engine (LTL model checking)...")
    with open(sat_output_file, "w") as f:
        sat_start_time = time.time()
        nuxmv_process = subprocess.run(
            ["nuxmv", model_filename],  # Use CTL model checking
            input=sat_commands,
            text=True,
            stdout=f,
            stderr=f
        )
    sat_end_time = time.time()
    sat_time = sat_end_time - sat_start_time
    # Validate SAT output
    results['sat_success'] = validate_nuxmv_execution(sat_output_file)

    # Return results
    results['bdd_output_file'] = bdd_output_file
    results['sat_output_file'] = sat_output_file
    results['bdd_time'] = bdd_time
    results['sat_time'] = sat_time
    return results


def extract_solution(nuxmv_output_file):
    """
    Extracts the solution from the NuXmv output file and filters out invalid characters.
    :param nuxmv_output_file: Path to the NuXmv output file.
    :return: The filtered solution as a string (only LURDlurd), or None if no solution is found.
    """
    with open(nuxmv_output_file, 'r') as f:
        lines = f.readlines()
        solution = []
        in_trace = False
        for line in lines:
            if "Trace Description" in line:
                in_trace = True
            if in_trace and ("shift_move" in line or "shift_push" in line):
                # Extract the shift value (e.g., "shift_move = d" or "shift_push = D")
                shift = line.split("=")[1].strip().strip('"')
                # Filter out invalid characters (only allow L, U, R, D, l, u, r, d)
                if shift.lower() in ['l', 'u', 'r', 'd']:
                    solution.append(shift)
            if in_trace and "-- Loop starts here" in line:
                # End of trace
                break
        if solution:
            return "".join(solution)
    return None


def save_solution(output_directory, solution_bdd, solution_sat, runtime_bdd, runtime_sat):
    """
    Saves the solution and runtime to a text file.
    :param output_directory: Directory to save the solution file.
    :param solution_bdd: The solution from the BDD engine.
    :param solution_sat: The solution from the SAT engine.
    :param runtime_bdd: The runtime of the BDD verification.
    :param runtime_sat: The runtime of the SAT verification.
    """
    solution_file = os.path.join(output_directory, "solution.txt")
    with open(solution_file, 'w') as f:
        f.write("BDD Engine Results:\n")
        if solution_bdd:
            f.write(f"Solution: {solution_bdd}\n")
        else:
            f.write("There is no solution.\n")
        f.write(f"Runtime: {runtime_bdd} seconds\n\n")

        f.write("SAT Engine Results:\n")
        if solution_sat:
            f.write(f"Solution: {solution_sat}\n")
        else:
            f.write("There is no solution.\n")
        f.write(f"Runtime: {runtime_sat} seconds\n")

    print(f"you can find the results in {output_directory}->solution.txt")


def main(input_board, output_directory):
    """
    Main function to handle the workflow: convert, run NuXmv, and save solutions.
    :param input_board: The XSB board content as a string.
    :param output_directory: Directory to save the outputs.
    """
    ensure_output_directory(output_directory)

    # Read the input XSB board file
    with open(input_board, 'r') as f:
        xsb_content = f.read()

    # Save the input XSB board file in the output directory
    input_board_copy = os.path.join(output_directory, os.path.basename(input_board))
    with open(input_board_copy, 'w') as f:
        f.write(xsb_content)

    # Convert the XSB board to SMV model
    smv_content = convert_xsb_to_smv(xsb_content)
    smv_file = os.path.join(output_directory, "model.smv")
    with open(smv_file, 'w') as f:
        f.write(smv_content)

    # Run the SMV model in nuXmv using both BDD and SAT engines
    results = run_nuxmv(smv_file, output_directory)

    # Extract the solution from nuXmv output
    solution_bdd = extract_solution(results['bdd_output_file'])
    solution_sat = extract_solution(results['sat_output_file'])

    # Save the solution and runtime
    save_solution(
        output_directory,
        solution_bdd,  # BDD solution
        solution_sat,  # SAT solution
        results['bdd_time'],  # BDD time
        results['sat_time']  # SAT time
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python v_sokoban.py <input_board> <output_directory>")
        sys.exit(1)
    input_board = sys.argv[1]
    output_directory = sys.argv[2]
    main(input_board, output_directory)
