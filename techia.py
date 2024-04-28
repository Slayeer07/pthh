class Literal:
    def __init__(self, name, is_negative=False):
        self.name = name
        self.is_negative = is_negative

    def __eq__(self, other):
        return isinstance(other, Literal) and self.name == other.name and self.is_negative == other.is_negative

    def __hash__(self):
        return hash((self.name, self.is_negative))

    def __repr__(self):
        return f"¬{self.name}" if self.is_negative else self.name

    def __str__(self):
        return f"!{self.name}" if self.is_negative else self.name

    def contrapositive(self):
        return Literal(self.name, not self.is_negative)

class Rule:
    def __init__(self, premises, conclusion, is_defeasible, name):
        self.premises = set(premises)
        self.conclusion = conclusion
        self.is_defeasible = is_defeasible
        self.name = name

    def __eq__(self, other):
        return (isinstance(other, Rule) and self.premises == other.premises and
                self.conclusion == other.conclusion and
                self.is_defeasible == other.is_defeasible and
                self.name == other.name)

    def __hash__(self):
        return hash((frozenset(self.premises), self.conclusion, self.is_defeasible, self.name))

    def __repr__(self):
        premises_str = ', '.join(map(str, self.premises))
        arrow = "=>?" if self.is_defeasible else "=>"
        return f"{self.name}: {premises_str} {arrow} {self.conclusion}"


    def contrapositive_rules(self):
        # Pour une règle sans prémisse, il n'y a pas de contraposition directe.
        if not self.premises:
            return []
        # Pour les règles avec prémisses, crée des règles de contraposition.
        contrapositive_rules = []
        for premise in self.premises:
            new_premises = self.premises.difference({premise})  # Enlève la prémisse actuelle
            new_premises.add(self.conclusion.contrapositive())  # Ajoute la négation de la conclusion
            new_conclusion = premise.contrapositive()  # La nouvelle conclusion est la négation de la prémisse
            contrapositive_rules.append(Rule(new_premises, new_conclusion, self.is_defeasible, ""))
        return contrapositive_rules



class Argument:
    def __init__(self, top_rule, sub_arguments, name):
        self.top_rule = top_rule  # expects a Rule object
        self.sub_arguments = set(sub_arguments)  # expects a set of Argument objects
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Argument) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        sub_arguments_str = ', '.join(map(str, self.sub_arguments))
        return f"{self.name}: Top rule: {self.top_rule}, Sub-arguments: {{{sub_arguments_str}}}"

    def get_defeasible_rules(self):
        """ Return the set of all defeasible rules used in this argument and its sub-arguments. """
        defeasible_rules = set()
        if self.top_rule.is_defeasible:
            defeasible_rules.add(self.top_rule)
        for sub_arg in self.sub_arguments:
            defeasible_rules.update(sub_arg.get_defeasible_rules())
        return defeasible_rules

    def get_last_defeasible_rules(self):
        """Return the set of last defeasible rules, i.e., the defeasible rules not used in sub-arguments of this argument."""
        if not self.sub_arguments:  # If there are no sub-arguments, return the top rule if it is defeasible
            return {self.top_rule} if self.top_rule.is_defeasible else set()

        last_defeasible_rules = self.get_defeasible_rules()  # Start with all defeasible rules

        # Remove the defeasible rules that are in sub-arguments
        for sub_arg in self.sub_arguments:
            last_defeasible_rules.difference_update(sub_arg.get_defeasible_rules())

        return last_defeasible_rules

    def get_all_sub_arguments(self):
        """ Return the set of all sub-arguments of this argument, including nested ones. """
        all_sub_args = set(self.sub_arguments)
        for sub_arg in self.sub_arguments:
            all_sub_args.update(sub_arg.get_all_sub_arguments())
        return all_sub_args




# Définir les règles strictes fournies
strict_rules = [
    Rule([], Literal('a'), False, 'r1'),
    Rule([Literal('b'), Literal('d')], Literal('c'), False, 'r2'),
    Rule([Literal('c', True)], Literal('d'), False, 'r3')
]

# Définir les règles défaisables fournies
defeasible_rules = [
    Rule([Literal('a')], Literal('d', True), True, 'r4'),
    Rule([], Literal('b'), True, 'r5'),
    Rule([], Literal('c', True), True, 'r6'),
    Rule([], Literal('d'), True, 'r7'),
    Rule([Literal('c')], Literal('e'), True, 'r8'),
    Rule([Literal('c', True)], Literal('r4', True), True, 'r9')
]

# Générer les contrapositions pour les règles strictes spécifiées
contrapositions = []
for rule in strict_rules:
    contrapositions.extend(rule.contrapositive_rules())

# Assigner les noms spécifiques r10, r11, r12 aux contrapositions
for i, rule in enumerate(contrapositions, start=10):
    rule.name = f"r{i}"

# Afficher les règles strictes et leurs contrapositions
print("---- Strict Rules and their Contrapositions ----")
for rule in strict_rules + contrapositions:
    print(f"{rule.name}: {', '.join(str(p) for p in rule.premises)} -> {rule.conclusion}")

    # Afficher les règles défaisables
print("\n---- Defeasible Rules ----")
for rule in defeasible_rules:
    print(f"{rule.name}: {', '.join(str(p) for p in rule.premises)} => {rule.conclusion}")

def parse_rules(input_text):
    rules = []
    lines = input_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extracting the rule name and body
        parts = line.split(':')
        if len(parts) < 2:
            continue  # Skip malformed lines
        rule_name = parts[0].strip()
        rule_body = parts[1].strip()

        # Determining defeasibility and splitting premises and conclusion
        is_defeasible = '=>' in rule_body
        split_char = '=>' if is_defeasible else '->'
        premises_part, conclusion_part = rule_body.split(split_char)
        premises = [parse_literal(p.strip()) for p in premises_part.split(',') if p.strip()]
        conclusion = parse_literal(conclusion_part.strip())

        rules.append(Rule(premises, conclusion, is_defeasible, rule_name))
    return rules

def parse_literal(literal_str):
    is_negative = literal_str.startswith('!')
    name = literal_str[1:] if is_negative else literal_str
    return Literal(name, is_negative)


import itertools

def generate_arguments(rules):
    arguments = []
    rule_to_argument = {}

    # Generate base arguments for rules without premises
    for rule in rules:
        if not rule.premises:
            argument = Argument(rule, [], f"A{len(arguments) + 1}")
            arguments.append(argument)
            rule_to_argument[(rule, frozenset())] = argument
            print(f"Base argument created: {argument}")

    # Generate complex arguments
    new_arguments_added = True
    while new_arguments_added:
        new_arguments_added = False
        for rule in rules:
            if rule.premises:
                all_combinations = itertools.product(*[
                    [arg for arg in arguments if arg.top_rule.conclusion == premise]
                    for premise in rule.premises
                ])
                for combo in all_combinations:
                    if (rule, frozenset(combo)) not in rule_to_argument:
                        argument = Argument(rule, combo, f"A{len(arguments) + 1}")
                        arguments.append(argument)
                        rule_to_argument[(rule, frozenset(combo))] = argument
                        new_arguments_added = True
                        print(f"New argument created: {argument}")

    return arguments


# We assume that strict_rules, defeasible_rules, and contrapositions are already defined lists of Rule objects.
combined_rules = strict_rules + defeasible_rules + contrapositions
all_arguments = generate_arguments(combined_rules)

# Print the arguments
for arg in all_arguments:
    premises = ', '.join(sub_arg.name for sub_arg in arg.sub_arguments)
    arrow = "=>?" if arg.top_rule.is_defeasible else "=>"
    print(f"{arg.name}: {premises} {arrow} {arg.top_rule.conclusion}")




for arg in all_arguments:
    defeasible_rules = arg.get_defeasible_rules()
    last_defeasible_rules = arg.get_last_defeasible_rules()
    all_sub_args = arg.get_all_sub_arguments()

    # Format the sets for printing
    defeasible_rules_str = ', '.join(rule.name for rule in defeasible_rules)
    last_defeasible_rules_str = ' '.join(rule.name for rule in last_defeasible_rules)
    all_sub_args_str = ', '.join(sub_arg.name for sub_arg in all_sub_args)


    # Print the details
    print(f" {arg.name}: Defeasible rule: {defeasible_rules_str}, Last Defeasible: {last_defeasible_rules_str}, Sub-Arguments: {all_sub_args_str}")

def generate_all_undercut(arguments):
    under = []
    for arg1 in arguments:
        for arg2 in arguments:
            # Check if arg2 is a sub-argument of arg1
            sub_arguments = arg2.get_defeasible_rules()
            arg1_conclusion = arg1.top_rule.conclusion
            arg1_conclusion_contrapositive = arg1.top_rule.conclusion.contrapositive()
            for sub_arg in sub_arguments:
                if (
                    arg2.top_rule.conclusion != arg1_conclusion_contrapositive and
                    arg1_conclusion.name == sub_arg.name

                ):
                    under.append((arg1, arg2))
    return under

# Assuming all_arguments is populated with Argument instances
undercuts = generate_all_undercut(all_arguments)

# Print the undercuts
for undercut in undercuts:
    print(f"{undercut[0].name} undercuts {undercut[1].name}")

def generate_rebuts(arguments):
    rebuts = []
    # For each argument, find if there is another argument that has the opposing conclusion.
    for i, arg1 in enumerate(arguments):
        for j, arg2 in enumerate(arguments):
            if i != j:  # Ensure we're not comparing an argument with itself.
                if arg1.top_rule.conclusion.contrapositive() == arg2.top_rule.conclusion:
                    rebuts.append((arg1, arg2))

    return rebuts

# Generate all rebuts for the set of arguments
rebuts = generate_rebuts(all_arguments)

# Print all rebuts
print(f"Total rebuts found: {len(rebuts)}")
for index, rebut in enumerate(rebuts, start=1):
    print(f"Rebut {index}: Argument {rebut[0].name} is rebutted by Argument {rebut[1].name}")

from flask import Flask, render_template, request

app = Flask(__name__, template_folder='.')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Parsing input from different text areas
        strict_rule_input = request.form['strict_rule_input']
        defeasible_rule_input = request.form['defeasible_rule_input']
        
        # Parse rules
        strict_rules = parse_rules(strict_rule_input)
        defeasible_rules = parse_rules(defeasible_rule_input)

        # Generate contrapositions for the strict rules
        contrapositions = []
        for rule in strict_rules:
            contrapositions.extend(rule.contrapositive_rules())
        for i, rule in enumerate(contrapositions, start=1):
            rule.name = f"rC{i}"

        # Combine all rules
        all_rules = strict_rules + defeasible_rules + contrapositions
        arguments = generate_arguments(all_rules)
        
        return render_template('results.html', arguments=arguments, contrapositions=contrapositions)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
