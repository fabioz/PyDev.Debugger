import sys
if __name__ == '__main__':

    a = [1, 2, 3, 4]
    b = [2, 7]

    assert any(x in a for x in b)

    def gen():
        yield 1

    for i in gen():
        pass

    def gen2():
        yield 2
        raise StopIteration()

    for i in gen2():
        pass

    print('TEST SUCEEDED!')
