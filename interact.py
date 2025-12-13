import example
from teacher import Teacher
from learner import RegisterAutomatonLearner
from dra import RegisterAutomaton
from alphabet import Alphabet

target = example.get_example_ra_3()
teacher = Teacher(target)
learner = RegisterAutomatonLearner(teacher, target.alphabet)
print(f"Initialisation ==============================================")
learner.start_learning()
learner.observation_table.pretty_print()

hypothesis = None
num_iterations = 0
counterexamples = [target.alphabet.make_sequence([4,5,4,5]), target.alphabet.make_sequence([1,0,1,2,1,2])]
while True:
        hypothesis = learner.get_hypothesis()
        print(f"Iteration {num_iterations} ==============================================")
        print("Current observation table:\n")
        learner.observation_table.pretty_print()
        print("\nCurrent Hypothesis:\n", hypothesis.to_dot())

        equivalent, counterexample = teacher.equivalence_query(
            hypothesis)

        if equivalent :
            break
        print("Counterexample found:", counterexamples[num_iterations])
        learner.refine_hypothesis(counterexamples[num_iterations])
        num_iterations += 1
print(f"Learning completed ==============================================")
print("Final Hypothesis:\n")
print(hypothesis.to_dot())
    