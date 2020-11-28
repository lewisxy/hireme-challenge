# python 3 is required
import os # to use os.random

# copied from challenge
diff = [0xf26cb481,0x16a5dc92,0x3c5ba924,0x79b65248,0x2fc64b18,0x615acd29,0xc3b59a42,0x976b2584,
0x6cf281b4,0xa51692dc,0x5b3c24a9,0xb6794852,0xc62f184b,0x5a6129cd,0xb5c3429a,0x6b978425,
0xb481f26c,0xdc9216a5,0xa9243c5b,0x524879b6,0x4b182fc6,0xcd29615a,0x9a42c3b5,0x2584976b,
0x81b46cf2,0x92dca516,0x24a95b3c,0x4852b679,0x184bc62f,0x29cd5a61,0x429ab5c3,0x84256b97]

# compute inverse using Gaussian-Jordan elimination
# bit_matrix is a 2d-array-like structure with number of rows=size and number of columns=size
def compute_inverse(bit_matrix, size):
    tmp_matrix = [[1 if i == j else 0 for i in range(size)] for j in range(size)]
    # create a deep copy as we will modify it
    bit_matrix = [[bit_matrix[i][j] for j in range(size)] for i in range(size)]
    #print("bit matrix after copy: {}".format(bit_matrix))

    # for every column
    for j in range(size):
        # for every row starting from j ( we know all columns before j are 0)
        flag = 0
        for i in range(j, size):
            # if we found a row that can be pivot on (for column j)
            if bit_matrix[i][j] == 1:
                # swap it to j
                tmp = bit_matrix[i]
                bit_matrix[i] = bit_matrix[j]
                bit_matrix[j] = tmp

                # also swap tmp_matrix
                tmp = tmp_matrix[i]
                tmp_matrix[i] = tmp_matrix[j]
                tmp_matrix[j] = tmp

                # assuming the matrix is invertible
                flag = 1
                #print("bit matrix after swap at {}th column: {}".format(j, bit_matrix))
                #print("inverse matrix after swap at {}th column: {}".format(j, tmp_matrix))
                break
        if flag == 0:
            print("warning: matrix not invertible")

        # then start to pivot, make all other rows this column 0
        for i in range(size):
            if i != j and bit_matrix[i][j] == 1:
                for k in range(size):
                    bit_matrix[i][k] ^= bit_matrix[j][k]
                    tmp_matrix[i][k] ^= tmp_matrix[j][k]
        #print("bit matrix after {}th column: {}".format(j, bit_matrix))
        #print("inverse matrix after {}th column: {}".format(j, tmp_matrix))
    
    #print("final bit matrix: {}".format(bit_matrix))
    #print("inverse matrix: {}".format(tmp_matrix))

    return tmp_matrix

# convert bit array to 32-bit unsigned integer
def bits_to_u32_reverse(bits):
    res = 0
    for i in range(32):
        res += bits[i] * 2 ** i
    return res

# convert 32-bit unsigned integer to bit array
def u32_to_bits_reverse(num):
    res = [0 for _ in range(32)]
    for i in range(32):
        bit = num % 2
        res[i] = bit
        num = num // 2
    return res

# for testing
def matrix_multiply_vector(a, b, size):
    res = [0 for i in range(size)]
    # print("a: {}".format(a))
    # print("b: {}".format(b))
    for i in range(size):
        for k in range(size):
            res[i] ^= (a[i][k] * b[k])
    return res

# verify the inverse is correct
def test_inverse():
    diff_matrix = list(map(lambda x: u32_to_bits_reverse(x), diff))
    inverse_diff_matrix = compute_inverse(diff_matrix, 32)
    inverse_diff = list(map(lambda x: bits_to_u32_reverse(x), inverse_diff_matrix))
    print(inverse_diff)

    output = bytearray(os.urandom(32))
    print("original output: {}".format(output))

    input_ = bytearray(32)
    input2 = bytearray(32)
    # diffuse round
    for j in range(32):
        for k in range(32):
            input_[j] ^= output[k] * ((diff[j] >> k) & 1)
    print("after diffuse: {}".format(input_))

    # diffuse with matrix
    input2 = matrix_multiply_vector(diff_matrix, output, 32)
    input2 = bytearray(input2)
    print("after matrix diffuse {}".format(input2)) # expecting same as above

    output_test = bytearray(32)
    output_test2 = bytearray(32)

    # inverse diffuse (suppose to undo diffuse)
    for j in range(32):
        for k in range(32):
            output_test[j] ^= input_[k] * ((inverse_diff[j] >> k) & 1)
    print("after inverse diffuse: {}".format(output_test))

    # inverse diffuse with matrix
    output_test2 = matrix_multiply_vector(inverse_diff_matrix, input2, 32)
    output_test2 = bytearray(output_test2)
    print("after matrix inverse diffuse {}".format(output_test2)) # expecting same as above


if __name__ == "__main__":
    test_inverse()
