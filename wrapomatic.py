import subprocess
import time
import json

"""An OOP library! OMG! Built and tested on a MacOS X (High Sierra).
This lib should be kept separate from other tools, because of its vulnerability
to dependency hell.

External programs wrapped:
HYPHY 2.3.720180108beta(MP).
baseml (PAML v4.8a, Aug 2014) - treesub.jar emulator only.

For the HYPHY wrappers, there's generally a problem where hyphy fails silently, in which case the Python
wrapper also fails silently, rather than printing an error inline. The user must watch the terminal 
screen to check hyphy's progress.
"""

class HyphySlac:
    """Wrapper class to call HYPHY SLAC.
    """
    def __init__(self):
        """
        self.branch_test_set
        --------------------
        Choose the set of branches to test for selection.
        1. [**All**] Include all branches in the analysis
        2. [**Internal**] Include all internal branches in the analysis
        3. [**Leaves**] Include all leaf branches in the analysis
        4. [**Unlabeled branches**] Set of 866 unlabeled branches
        5. [**test**] Set test with 49 branches

        self.num_ancestors
        ------------------
        Select the no. of samples used to assess
        ancestral reconstruction uncertainty. Choose 0 to skip.
        Permissible range = [0,100000], default value = 100, integer.
        self.p_val_threshold: Select the p-value threshold to use when testing
        for selection. Permissible range = [0,1], default value = 0.1.
        """
        self.analysis_type="1" # Selection analysis
        self.analysis_subtype="3" # SLAC
        self.genetic_code="1" # Universal genetic code
        self.data_file = ""
        self.use_tree="y" # Use the tree file in the input data_file.
        self.branch_test_set="1"
        self.num_ancestors="100"
        self.p_val_threshold="0.1"

    def get_cmd_str(self, outfile_suffix="_results.out"):
        """WIP"""
        print("wip")


class HyphyRelax:
    """Wrapper class to call HYPHY RELAX. So far, only supports 1 input file
    containing both the sequence and tree data; doesn't support those two bits
    as separate files.
    """
    def __init__(self):
        """
        self.branch_test_set
        --------------------
        the set of branches to use as the _test_ set
        1. [**Unlabeled branches**] Set of unlabeled branches
        2. [**test**] Set test with branches

        self.relax_analysis_type
        ------------------------
        RELAX analysis type
        1. [**All**] (Default)Fit descriptive models AND run the relax test (4 models)
        2. [**Minimal**] Run only the RELAX test (2 models)
        """
        self.analysis_type="1" # Selection analysis
        self.analysis_subtype="7" # RELAX
        self.genetic_code="1" # Universal genetic code
        self.data_file="" # input data file, with both sequence and tree data.
        self.use_tree="y" # Use the tree file in the input data_file.
        self.branch_test_set="2" # Use labelled branches. 1 = Use unlabelled.
        self.relax_analysis_type="2" # Run only 2 model. 1 = run 4 models.
        self.output_suffix="_results.out" # output file suffix

    def get_cmd_str(self):
        """Get a single bash command string. There's probably a better way to
        do this.
        """
        cmd1 = "(echo "+self.analysis_type+"; "
        cmd2 = "echo "+self.analysis_subtype+"; "
        cmd3 = "echo "+self.genetic_code+"; "
        cmd4 = "echo "+self.data_file+"; "
        cmd5 = "echo "+self.use_tree+"; "
        cmd6 = "echo "+self.branch_test_set+"; "
        cmd7 = "echo "+self.relax_analysis_type+") "
        #cmd_suffix = "| HYPHYMP > "+self.data_file+self.output_suffix
        cmd_suffix = "| HYPHYMP"

        cmd = cmd1 + cmd2 + cmd3 + cmd4 + cmd5 + cmd6 + cmd7 + cmd_suffix

        return cmd

    def run(self, run_type="inline", write_out_fn="run.txt", verbose=True):
        """Wrapper function for get_cmd_str() to run it.

        Params
        ------
        run_type: str.
            "inline": runs in a subprocess.run()
            "write_out": writes out a text file to bash externally.
        write_out_fn: str. Only used for run_type "write_out". The name of the
        text file to write out the command string to.
        verbose: bool; verbosity param.
        """
        relax_disp_dict = {"1": "(Default)Fit descriptive models AND run the relax test (4 models",
                           "2": "Run only the RELAX test (2 models)"}

        br_disp_dict = {"1": "Set of unlabeled branches",
                        "2": "Branches labelled 'test'"}

        if verbose:
            print("Running HYPHYMP:RELAX")
            print("Genetic code = universal code")
            print("Input file = %s" % self.data_file)
            print("Branches used as _test_ set:", end=" ")
            print(br_disp_dict[self.branch_test_set])
            print("RELAX analysis type:", end=" ")
            print(relax_disp_dict[self.relax_analysis_type])
            print("STDOUT output file: %s" % self.data_file+self.output_suffix)

        if run_type=="inline":
            t0 = time.time()

            cmd = self.get_cmd_str()
            subprocess.run(cmd, shell=True)

            if verbose:
                print("Done in %.2fs" % (time.time() - t0))


    def show_me(self):
        """Human Helper: Displays all current attributes and values of the
        HyphyRelax object.
        """
        print("analysis_type = %s" % self.analysis_type)
        print("analysis_subtype = %s" % self.analysis_subtype)
        print("genetic_code = %s" % self.genetic_code)
        print("data_file = %s" % self.data_file)
        print("use_tree = %s" % self.use_tree)
        print("branch_test_set = %s" % self.branch_test_set)
        print("relax_analysis_type = %s" % self.relax_analysis_type)
        print("output_suffix = %s" % self.output_suffix)


def parse_relax_json(fn_in, verbose=True):
    """Reads the JSON output of a default HyphyRelax.run(), and prints out the
    output. WARNING: Only built and tested for default run params!
    """
    json_data=open(fn_in).read()
    data = json.loads(json_data)

    fits_dict = data.get("fits")
    dict1 = fits_dict.get("MG94xREV with separate rates for branch sets")
    m0 = fits_dict.get("RELAX null")
    m1 = fits_dict.get("RELAX alternative")
    if verbose:
        print("GLOBAL dNdS VALUES")
        print("-"*20)
        print("AIC-c = %s" % dict1.get("AIC-c"))
        print("LogL = %s" % dict1.get("Log Likelihood"))
        print("dNdS ratio for *Reference* = %s" %
              dict1.get("Rate Distributions").get("non-synonymous/synonymous rate ratio for *Reference*")[0][0])
        print("dNdS ratio for *Test* = %s" %
             dict1.get("Rate Distributions").get("non-synonymous/synonymous rate ratio for *Test*")[0][0])
        print("")

        print("M0: k = 1")
        print("-"*20)
        print("REFERENCE & TEST BRANCHES")
        print("AIC-c = %.5f" % m0.get("AIC-c"))
        print("LogL = %.5f" % m0.get("Log Likelihood"))
        m0_ref_dict = m0.get("Rate Distributions").get("Reference")
        for k in list(m0_ref_dict.keys()):
            print("Class %s: omega = %.5f, proportion = %.5f%%" % (k,
                                                             m0_ref_dict[k]["omega"],
                                                             m0_ref_dict[k]["proportion"]*100))
        print("")

        print("M1: k != 1")
        print("-"*20)
        print("REFERENCE & TEST BRANCHES")
        print("AIC-c = %.5f" % m1.get("AIC-c"))
        print("LogL = %.5f" % m1.get("Log Likelihood"))
        m1_ref_dict = m1.get("Rate Distributions").get("Reference")
        m1_test_dict = m1.get("Rate Distributions").get("Test")
        for k in list(m1_ref_dict.keys()):
            print("Class %s: omega = %.5f, proportion = %.5f%%" % (k,
                                                             m1_ref_dict[k]["omega"],
                                                             m1_ref_dict[k]["proportion"]*100))
        print("")
        for k in list(m1_test_dict.keys()):
            print("Class %s: omega = %.5f, proportion = %.5f%%" % (k,
                                                             m1_test_dict[k]["omega"],
                                                             m1_test_dict[k]["proportion"]*100))

        print("")
        print("LRT RESULTS")
        print("-"*20)
        print("LRT = %.5f" % data.get("test results").get("LRT"))
        print("p-value = %.5f" % data.get("test results").get("p-value"))
        print("k = %.5f" % data.get("test results").get('relaxation or intensification parameter'))
