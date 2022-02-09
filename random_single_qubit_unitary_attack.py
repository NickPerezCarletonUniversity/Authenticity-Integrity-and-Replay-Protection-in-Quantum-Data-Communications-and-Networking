#This code correspondes to Figure 4.A in "Authenticity, Integrity and Replay Protection in Quantum DataCommunications and Networking"
#Please cite our paper when using this code

import time
import numpy as np
import utilities
import random

start = time.time()
num_trials = 50
#max_total_qubits = 9
max_total_qubits = 5
#this parameter is for determining how many different sets of random states to experiment on
#the entire experiment setup is repeated 'num_states_per_qubit_size' number of times, with
#each repetition using a different set of random states
num_states_per_qubit_size = 1
for j in range(num_states_per_qubit_size):
    num_detections_array = np.full([max_total_qubits - 1, max_total_qubits - 1], float("nan"))
    for num_signature_qubits in range(1,max_total_qubits):
        for num_data_qubits in range(1,max_total_qubits - num_signature_qubits + 1):
            num_detections = 0
            curr_total_qubits = num_data_qubits + num_signature_qubits
            data_to_encrypt = utilities.generate_data_to_encrypt(curr_total_qubits, num_signature_qubits)

            for trial in range(num_trials):
                result = -1
                while result == -1:
                    #The adversary applies a random unitary
                    adversarial_attack = utilities.get_adversarial_attack_circuit(curr_total_qubits,random.randint(0, curr_total_qubits-1))

                    result = utilities.adversary_simulation_clifford_encryption(curr_total_qubits, num_signature_qubits, adversarial_attack, data_to_encrypt)

                    if result == 1:
                        num_detections = num_detections + 1

            
            print("number of data qubits = " + str(num_data_qubits))
            print("number of signature qubits = " + str(num_signature_qubits))
            print("Detected " +  str(num_detections) + " integrity attacks")
            print("Detected integrity attacks in " + str(100 * num_detections/num_trials) + "% of the time")
            print()
            num_detections_array[num_data_qubits-1,num_signature_qubits-1] = num_detections
    print(num_detections_array)
    end = time.time()
    print("Time to complete: " + str(end - start) + " seconds")
    np.save("num_detections_array_" + str(j) + "_for_" + str(num_trials) + "_num_trials",num_detections_array)
