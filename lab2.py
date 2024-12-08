from dataclasses import dataclass
from typing import List, Tuple
import sys
import copy

# Author: Connor McRoberts
free_variable_counter = 0
type_dict: dict[str, str] = {}

@dataclass
class Function:
    name: str
    terms: List[str]

    # example of what we are working with 'SKF1(x4)'
    def __init__(self, f_string):
        self.terms = []
        curr_pointer = 0
        start_name_p = 0
        while curr_pointer < len(f_string) and f_string[curr_pointer] != '(':
            curr_pointer += 1
        self.name = f_string[start_name_p: curr_pointer]

        curr_pointer += 1
        while curr_pointer < len(f_string) and f_string[curr_pointer] != ')':
            start_term_f = curr_pointer
            while curr_pointer < len(f_string) and f_string[curr_pointer] != ',' and f_string[curr_pointer] != ')':
                curr_pointer += 1
            self.terms.append(f_string[start_term_f : curr_pointer])
            curr_pointer += 1

    def to_string(self) -> str:
        f_string = self.name + "("
        for i in range(self.terms - 1):
            f_string += (self.terms[i] + ',')
        f_string += (self.terms[len(self.terms) - 1] + ")")

        return f_string
    



        


class Predicate:
    name: str
    negated: bool
    terms: List[str]
    functions: List[Function]
    p_string: str # useful for debugging and hashing

    def __hash__(self) -> int:
        return hash(self.p_string)

    def __init__(self, p_string: str):
        self.p_string = p_string
        self.terms = []
        self.functions = []
        curr_pointer = 0 # keep track of where we are parsing the string
        if (p_string[curr_pointer] == '!'):
            self.negated = True
            curr_pointer += 1
        else:
            self.negated = False
        # get the name of the predicate
        start_name_p = curr_pointer
        while curr_pointer < len(p_string) and p_string[curr_pointer] != '(':
            curr_pointer += 1
        self.name = p_string[start_name_p: curr_pointer]
        # get the terms

        made_function = False
        curr_pointer += 1
        while curr_pointer < len(p_string) and p_string[curr_pointer] != ')':
            start_term_p = curr_pointer
            while curr_pointer < len(p_string) and p_string[curr_pointer] != ',' and p_string[curr_pointer] != ')':
                # look incase if it is a function
                if p_string[curr_pointer] == '(':
                    self.terms.append(p_string[start_term_p: curr_pointer])
                    while curr_pointer < len(p_string) and p_string[curr_pointer] != ')':
                        curr_pointer += 1
                    curr_pointer += 1
                    self.functions.append(Function(p_string[start_term_p: curr_pointer]))
                    made_function = True

                curr_pointer += 1
            # loop came across a ',' or a ')' make a new term
            if not made_function:
                self.terms.append(p_string[start_term_p: curr_pointer])
            made_function = False
            curr_pointer += 1
        

    def __eq__(self, value: object) -> bool:
        if (not isinstance(value, Predicate) or self.name != value.name or self.negated != value.negated):
            return False
        
        if (len(self.terms) != len(value.terms)):
            return False
        
        for i in range(len(self.terms)):
            if (self.terms[i] != value.terms[i]):
                return False
        
        for i in range(len(self.functions)):
            if (self.functions[i] != value.functions[i]):
                return False
        return True
     
    
    def unifiable(self, value: object) -> tuple[bool, dict[str, str]]:
        """
        Checks if the two predicates can be unified.
        For that to happen the two need:
        - same name
        - same terms
        - one is negated and one is not
        """
        global free_variable_counter
        if (not isinstance(value, Predicate) or self.name != value.name or self.negated == value.negated):
            return (False, {})
        
        if (len(self.terms) != len(value.terms)):
            return (False, {})
        
        terms_substituted: dict[str, str] = {}
        for i in range(len(self.terms)):
            # only handle free variable substitution when unified, dont add
            # new free variables to kb
            if (self.terms[i] != value.terms[i]):
                if type_dict[self.terms[i]] == "variable" and self.terms[i] not in terms_substituted:
                    terms_substituted[self.terms[i]] = value.terms[i] # x was subbed for y
                    #print(f"Substituting {value.terms[i]} for {self.terms[i]} in {self.p_string}, {value.p_string}")
                elif type_dict[value.terms[i]] == "variable" and value.terms[i] not in terms_substituted:
                    terms_substituted[value.terms[i]] = self.terms[i]
                    #print(f"Substituting {self.terms[i]} for {value.terms[i]} in {value.p_string}, {self.p_string}")
                elif (type_dict[self.terms[i]] == "variable" and type_dict[value.terms[i]] == "variable" 
                and value.terms[i] not in terms_substituted and self.terms[i] not in terms_substituted):
                    free_variable_counter += 1
                    v = ("x" + free_variable_counter)
                    terms_substituted[self.terms[i]] = v
                    terms_substituted[value.terms[i]] = v
                    #print(f"Substituting {value.terms[i]} and {self.terms[i]} for a new free variable ({v}) in {value.p_string}, {self.p_string}")
                # if both term types are functions, see if there terms can be substituted to be unified
                elif type_dict[self.terms[i]] == "function" and type_dict[value.terms[i]] == "function":
                    for f in self.functions:
                        if f.name == self.terms[i]: 
                            self_func = f
                            break
                    for f in value.functions:
                        if f.name == value.terms[i]:
                            value_func = f
                            break
                    if len(self_func.terms) != len(value_func.terms):
                        return (False, {})
                    for i in self_func.terms:
                        if self_func.terms[i] != value_func.terms[i]:
                            if type_dict[self_func.terms[i]] == "variable" and self_func.terms[i] not in terms_substituted:
                                terms_substituted[self_func.terms[i]] = value_func.terms[i]
                                #print(f"Substituting {value_func.terms[i]} for {self_func.terms[i]} in {self.p_string}, {value.p_string}")
                            elif type_dict[value_func.terms[i]] == "variable" and value_func.terms[i] not in terms_substituted:
                                terms_substituted[value_func.terms[i]] = self_func.terms[i]
                                #print(f"Substituting {self_func.terms[i]} for {value_func.terms[i]} in {value.p_string}, {self.p_string}")
                            elif (type_dict[self_func.terms[i]] == "variable" and type_dict[value_func.terms[i]] == "variable" 
                            and value_func.terms[i] not in terms_substituted and self_func.terms[i] not in terms_substituted):
                                free_variable_counter += 1
                                v = ("x" + free_variable_counter)
                                terms_substituted[self_func.terms[i]] = v
                                terms_substituted[value_func.terms[i]] = v
                                #print(f"Substituting {value_func.terms[i]} and {self_func.terms[i]} for a new free variable ({v}) in {value.p_string}, {self.p_string}")
                else:
                    return (False, {})
        
        # it passes all checks

        return (True, terms_substituted)
    
    


class KB:
    clauses: List[List[Predicate]]

    def __init__(self):
        self.clauses = []

def compose_kb(file_name: str) -> KB:
    try:
        with open(sys.argv[1], 'r') as file:
            global free_variable_counter
            kb = KB()
            line = file.readline().split()
            # add predicates to dict for identification
            if line[0] != "Predicates:":
                print("File is not formatted correctly")
                exit(1)
            for i in range(1, len(line)):
                type_dict[line[i]] = "predicate"
            line = file.readline().split()
            while (len(line) != 0 and line[0] != "Variables:"):
                for i in range(len(line)):
                    type_dict[line[i]] = "predicate"
                line = file.readline().split()
            # add variables to dict for identification
            for i in range(1, len(line)):
                type_dict[line[i]] = "variable"
                free_variable_counter += 1
            line = file.readline().split()
            while (len(line) != 0 and line[0] != "Constants:"):
                for i in range(len(line)):
                    type_dict[line[i]] = "variable"
                    free_variable_counter += 1
                line = file.readline().split()
            # add constant names to dict for identification
            for i in range(1, len(line)):
                type_dict[line[i]] = "constant"
            while (len(line) != 0 and line[0] != "Functions:"):
                for i in range(len(line)):
                    type_dict[line[i]] = "constant"
                line = file.readline().split()
            # add function names to dict for identification
            for i in range(1, len(line)):
                type_dict[line[i]] = "constant"
            while (len(line) != 0 and line[0] != "Clauses:"):
                for i in range(len(line)):
                    type_dict[line[i]] = "constant"
                line = file.readline().split()
            
            # assumption: all example files have "Clauses: " on its own line.
            # therfore we can skip a line
            predicates = file.readline().split()
            while (len(predicates) != 0):
                clause = []
                for p in predicates:
                    clause.append(Predicate(p))
                kb.clauses.append(clause)
                predicates = file.readline().split()
                    
            return kb
    except FileNotFoundError:
            print(f"Error: Could not find a text file with the name {sys.argv[1]}")
    except IOError:
            print(f"Error: A problem occured attempting to read {sys.argv[1]}")  

def clauses_unifiable(c1: List[Predicate], c2: List[Predicate]) -> Tuple[bool, List[List[Predicate]]]:
    """
    Returns a boolean telling us if the two clauses are unifiable and if they are,
    it returns the all new clauses that could be generated to add to our knowledge base.
    """
    # check if any two predicates can be negated
    can_be_unified = False
    generated_clauses = []
    for p1 in c1:
        for p2 in c2:
            u = p1.unifiable(p2)
            if u[0]:
                can_be_unified = True
                unified_clause: List[Predicate] = []
                for p in c1:
                    if p != p1:
                        unified_clause.append(copy.deepcopy(p))
                for p in c2:
                    if p != p2:
                        unified_clause.append(copy.deepcopy(p))
                for p in unified_clause:
                    for i in range(len(p.terms)):
                        if (p.terms[i] in u[1]):
                            p.terms[i] = u[1][p.terms[i]]

                generated_clauses.append(unified_clause)

    
    if (can_be_unified == False):
        return (can_be_unified, None)
    
    return (can_be_unified, generated_clauses) 
     

def isSatisfiable(kb: KB):
    # loop until no more substitutions and/unifications can be found
    # 2 steps
    # loop through clauses in db, sustitute all free variables for every constant,
    # creating new clauses in the kb
    # attempt to unify as many clauses as possible.

    already_checked: dict[Tuple[Tuple[Predicate]], bool] = {}
    while True:
        # loop over all possible combinations, dont check ones that have already been checked
        len_of_checked_combos = 0
        for cl1 in kb.clauses:
            for cl2 in kb.clauses:
                t1 = tuple(cl1)
                t2 = tuple(cl2)
                if (t1, t2) not in already_checked:
                    is_unifiable = clauses_unifiable(cl1, cl2)
                    if is_unifiable[0]:
                        for clause in is_unifiable[1]:
                            kb.clauses.append(clause)
                            # empty set found, it is not satasfiable
                            if len(clause) == 0:
                                print("no")
                                exit()
                    already_checked[(t1, t2)] = True
                else:
                    len_of_checked_combos += 1
                # is not making any new clauses, it is satasfiable
                # print(f"length of clauses: {len(kb.clauses)}, length of already_checked: {len(already_checked)}")
        if len_of_checked_combos == (len(kb.clauses) * len(kb.clauses)):
            print('yes')
            exit()

        





def main():
    if len(sys.argv) != 2:
        print(f"Error: Expected 1 arguement but received {len(sys.argv) - 1}.")
        sys.exit(1)
    kb = compose_kb(sys.argv[1])
    isSatisfiable(kb)

if (__name__ == "__main__"):
    main()

# Biggest TODO s 1. make subsitution for functions, 