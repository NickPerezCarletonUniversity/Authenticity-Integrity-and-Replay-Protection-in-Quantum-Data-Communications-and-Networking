from qiskit.quantum_info import random_statevector, Statevector, Operator, random_clifford
from qiskit import QuantumCircuit
import numpy as np
import random
from scipy.stats import unitary_group
import matplotlib.pyplot as plt
import math
import os

#returns a random state vector for the data qubits, and initializes all signature qubits to |0>
def generate_data_to_encrypt(num_total_qubits, num_signature_bits):
    signature_qubits = Statevector(np.concatenate((np.ones(1),np.zeros((2 ** num_signature_bits)-1)),axis=0))
    data_qubits = random_statevector(2**(num_total_qubits - num_signature_bits))
    data_to_encrypt = Statevector(np.kron(data_qubits, signature_qubits))
    return data_to_encrypt

#returns an adversarial attack circuit where the adversary applies a single qubit unitary to a qubit in the encrypted data, 
#if 'qubit_position_to_attack' is not specified, the adversary applies the unitary to a random qubit position
#if 'operation_to_apply' is not specified, the adversary applies a random unitary to the specified position
def get_adversarial_attack_circuit(num_total_qubits, qubit_position_to_attack = -1, operation_to_apply=None):
    if qubit_position_to_attack == -1:
        qubit_position_to_attack = random.randint(0, num_total_qubits - 1)
    qc = QuantumCircuit(num_total_qubits)
    if operation_to_apply is None:
        while True:
            random_unitary = unitary_group.rvs(2)
            qc.unitary(random_unitary,qubit_position_to_attack)
            if not np.array_equal(random_unitary, np.identity(2)):
                break
            else:
                print("randomly selected the identity!")
    else:
        qc.unitary(operation_to_apply,qubit_position_to_attack)
    return qc

def adversary_simulation_common(qc, num_total_qubits, num_signature_bits, adversarial_attack, data_to_encrypt):
    encrypted_data = data_to_encrypt.evolve(qc)
    attacked_data = encrypted_data.evolve(adversarial_attack)
    decrypted_data = attacked_data.evolve(Operator(qc).adjoint())
        
    measurement_result, resulting_state_vector = decrypted_data.measure(list(range(num_signature_bits)))
    if resulting_state_vector == data_to_encrypt:
        print("the adversary had no effect on the state!")
        return -1
    if '1' in str(measurement_result):
        return 1
    return 0

#simulates a given adversarial attack assuming the encryption is done using a random clifford
#other types of operations may be used for ecnryption
def adversary_simulation_clifford_encryption(num_total_qubits, num_signature_bits, adversarial_attack, data_to_encrypt):
    qc = random_clifford(num_total_qubits).to_circuit()
    return adversary_simulation_common(qc, num_total_qubits, num_signature_bits, adversarial_attack, data_to_encrypt)

#https://stackoverflow.com/questions/10029588/python-implementation-of-the-wilson-score-interval
#https://www.dummies.com/education/math/statistics/checking-out-statistical-confidence-interval-critical-values/
def wilson_score_confidence(successes, trials, z):
    n = trials

    if n == 0:
        return 0

    phat = float(successes) / n
    upper_bound = ((phat + z*z/(2*n) + z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n))
    lower_bound = ((phat + z*z/(2*n) - z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n))
    return lower_bound, upper_bound

#generates 3D bar graphs from all previously saved trials
#https://matplotlib.org/stable/gallery/mplot3d/3d_bars.html
def generate_graphs(num_trials,bar_width = 0.5,bar_depth = 0.5):
    for filename in os.listdir():
        if filename.endswith(".npy"):
            generate_graph(filename,num_trials)

#generates a 3D bar graph of an trial with a confidence interval on each bar
#set both bar_width and bar_depth to 0.5 when doing small amounts of qubits
#might have to experiment a bit with different depths and widths to get a pretty graph
#there is a known issue with not being able to change the scale of axes in 3D bar graphs
#using matplot lib
def generate_graph(filename,num_trials,bar_width = 0.5,bar_depth = 0.5):
    data_unfiltered = np.load(filename)

    # setup the figure and axes
    fig = plt.figure(figsize=(12, 12))
    ax1 = fig.add_subplot(121, projection='3d')

    x_unfiltered, y_unfiltered = np.mgrid[1:data_unfiltered.shape[0]+1,1:data_unfiltered.shape[1]+1]
    x_unfiltered = x_unfiltered.ravel()
    y_unfiltered = y_unfiltered.ravel()

    data_unfiltered = data_unfiltered.ravel()
    data_lower_bound = []
    data_upper_bound = []
    x = []
    y = []
    z_value = 1.96
    for i in range(data_unfiltered.shape[0]):
        if not math.isnan(data_unfiltered[i]):
            data_lower_bound.append(wilson_score_confidence(data_unfiltered[i],num_trials,z_value)[0])
            data_upper_bound.append(wilson_score_confidence(data_unfiltered[i],num_trials,z_value)[1])
            x.append(x_unfiltered[i])
            y.append(y_unfiltered[i])


    bottom = np.zeros_like(data_lower_bound)

    confidence_interval_size = np.array(data_upper_bound) - np.array(data_lower_bound)

    ax1.bar3d(x, y, bottom, bar_width, bar_depth, data_lower_bound, shade=True)
    ax1.bar3d(x, y, data_lower_bound, bar_width, bar_depth, confidence_interval_size, shade=True, color='#00ceaa')
    ax1.set_title('Effectiveness of Integrity Detection in Encrypted Quantum Data')
    ax1.set_xlabel("Number of data qubits (m)")
    ax1.set_ylabel("Number of authentication qubits (d)")
    ax1.set_zlabel("Probability of detection")

    ax1.tick_params(axis='x', length=1, width=1, pad = 1)
    ax1.tick_params(axis='y', length=1, width=1, pad = 1)


    plt.savefig(os.path.splitext(filename)[0]+'.png', format='png', bbox_inches='tight',pad_inches = 0, dpi=900)
    plt.show()

generate_graphs(100)