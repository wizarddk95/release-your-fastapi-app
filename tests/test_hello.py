# assert는 "이 조건은 반드시 참이어야 한다"라고 프로그램에게 선언하는 문법.
# 조건이 False라면 즉시 에러를 발생시킴

def test_hello():
    assert 1 + 2 == 3 

 
def add(a, b):
    return a + b


def test_add():
    assert add(1, 2) == 3