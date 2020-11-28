# hireme-challenge
My solution to the challenge https://www.nerd.nintendo.com/files/HireMe

## Write up
The puzzle consists of 3 parts, **confusion** (lookup table replacement), **diffusion** (double for-loop), and **compression** (the last step, compress 32 bytes to 16 bytes).
On the high level,
```c
void Forward(u8 input[32], u8 output[32], u8 conf[512], u32 diff[32]) {
    for (u32 i = 0; i < 256; i++) {
        // confusion
        for (u8 j = 0; j < 32; j++) {
            output[j] = conf[input[j]];
            input[j] = 0;
        }

        // diffusion
        for (u8 j = 0; j < 32; j++)
            for (u8 k = 0; k < 32; k++)
                input[j] ^= output[k] * ((diff[j] >> k) & 1);
    }
    // compression
    for (u8 i = 0; i < 16; i++)
        output[i] = conf[input[i*2]] ^ conf[input[i*2+1] + 256];
}
```
can be written as
```python
def forward(input_, output):
    for i in range(256):
        output = confusion(input_)
        input_ = diffusion(output)
    output = compression(input_)
```
or
```
output = compression(diffusion(confusion(...diffusion(confusion(input)))...)))
```
There are 256 alternating rounds of confusion and diffusion.
To solve this puzzle, the high level idea is to undo all these operations one-by-one and thus compute the input from a given output.

### Diffusion
Diffusion is the easiest part as it's essentially a matrix multiplication (32x32 binary matrix), and that matrix happens to be invertible.
```c
for (u8 j = 0; j < 32; j++)
    for (u8 k = 0; k < 32; k++)
        input[j] ^= output[k] * ((diff[j] >> k) & 1);
```
is equivalent to
```
input(32x1) = diffusion_matrix(32x32) * output(32x1)
```
If we can find the inverse matrix, we can easily undo this part.
```
output(32x1) = inverse_diffusion_matrix(32x32) * input(32x1)
```
See [compute_inverse.py](compute_inverse.py) for detail.

### Compression
<!-- The confuson array has 512 bytes. Since a byte has 256 values, we can treat it as 2 lookup tables.
The confusion part uses only the first half, and the compression part uses both. -->
Compression is also pretty straight forward. It's an element-wise operation, turning every 2 bytes to 1 byte.

<!-- However, since it is a 32-byte to 16-byte function, a particular output of compression can have many valid inputs, 2^128 to be exact.
To find a particular 32-byte input for a given output, we can just loop over the first table, xor the byte in output with that value, then try to find the result in the second table. -->

On a high level, for each byte produced by the compression (let's call the first and second half of confusion array `conf1` and `conf1`),
```
output_byte = conf1[byte] ^ conf2[byte]
```
We can rewrite the equation to
```
conf2[byte] = output_byte ^ conf1[byte]
```
Therefore, given an output byte, we can find a possible input as the following
```
# idx can be any byte (or we can just loop through all possible bytes)
candidate_for_conf2 = output_byte ^ conf1[idx]
idx2 = conf2.index(candidate_for_conf2) # there might be 0, 1, or multiple idx2
a possible inverse for output_byte = (idx, idx2) # if idx2 exist
```
We can generate a lookup table encoding all possible pair of bytes for each `output_byte` easily (see `compute_expansion_map` in  [solve.py](solve.py)).

### Confusion
Confusion is the most difficult part of the entire puzzle. 
It's tempting to think that a simple inverse lookup table can undo this operation.
However, because some values in the confussion array showed up multiple times, we cannot unambiguiously find an input byte from an output byte.
And even worse, some output bytes has no input byte associated with it.
In other words, it's not a one-to-one function, and thus no inverse (the puzzle would be trivial if there confusion is invertible).

Because confusion is performed 256 rounds, we need a systematic way to try all possibilities with the following logics.
1. If there is more than 1 ways to undo confusion round, try all of them.
2. If there is no way to undo confusion, backtrack to previous step.
3. Obviously, if there is an unambiguious way to undo the round, just do it.

Think about this operation as exploring a "tree".
At a given node (a possible input awating undoing confusion round), logic 1 suggests there is multiple children, in which we need to explore all of them.
Logic 2 suggests we arrived at a leaf node, if we haven't reached the desired depth (256 rounds), we hit an dead end.
Logic 3 suggests there is one child, and we need to explore that.

Therefore, we can implmenet a recursive backtracking algorithm (a special case for DFS) to explore this "tree", and terminates either when all path failed, or when we get through 256 rounds.
Of course, the input for this part is the output from undoing the compression.
Since there is also many possible output from that part, if a particular input failed (i.e. all reached dead end), we can move on to the next one, until we find a solution.

See `solve` in  [solve.py](solve.py) for implementation details.

<!-- below are WIP, please don't read -->
<!-- ### Algorithm analysis
Does this algorithm work?
Of course not, unless we are really lucky.

We don't know how large a "tree" is.
If each node has k children on average, it will take roughly m^256 operations to explore the tree in the worst case (i.e. we always hit dead end on 255th try).
This means if k >= 2, the algorithm will take an astronomical amount of time to run (basically no different from brute-forcing the 32-byte input in the beginning), not to mention there is 2^128 possible input (generated by undoing the compression) to begin with in the worst case.

Fortunately, we don't always hit dead end on last try, suppose there are m out of 256 values cannot be reversed.
Assuming diffusion round is a perfect hash function that each byte is independent and equally likely for random input, there is a m/256 chance per byte that we cannot reverse the operation.
Because we cannot undo the confusion round (i.e. hit an dead end) if we fail to reverse for any byte, the probability of failure for a 32 byte input is p = 1 - ((256-m)/m)^32.
If we did not failed, on average, each byte can be translated to 256 / (256 - m) bytes, so there is k = (256 / (256 - m))^32 branches to explore.
And we know maximum tree height H = 256.
Given these information, let E(p, k, H) be the expected number nodes in tree (a tree with n nodes always has n-1 branches, which is a rough measure of number of operations)
We can write the recurrance relationship for E, assuming `E(p, k, 0) = 1`:
```
E(p, k, H) = p * 1 + (1 - p) * k * E(p, k, H-1)
```
Because `(1 - p) * k = 1` in our case, `E(p, k, H) = pH <= H`. This means on average it will take no more than 256 operations to explore a "tree" (either reject the output).

The remaining question is how many inputs after undoing the compression is valid, which is impossible to know without deep inspection of the the confusion array. -->


