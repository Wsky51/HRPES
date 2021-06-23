import math

#埃拉托色尼筛选法,返回1~n内所有的素数，时间复杂度o(nlogn)
def eratosthenes(n):
    visit=[False]*(n+1)
    m= int(math.sqrt(n+0.5))
    for i in range(2,m+1):
        if (not visit[i]):
            for j in range(i*i,n+1,i):
                visit[j]=True
    res=list()
    for i in range(2,n+1):
        if not visit[i]:
            res.append(i)
    return res

#计算a,b的最大公约数
def gcd(a,b):
    if a<b:
        temp=a
        a=b
        b=temp
    while (b != 0):
        temp = a % b
        a=b
        b=temp
    return a

#计算快速幂
def fast_pow(x,pow):
    res = 1
    while(pow != 0):
        if ((pow & 1) == 1):
            res = res * x
        pow=pow//2
        x=x*x
    return res

#求x在mod的情况下的乘法逆元，前提是gcd(x,mod)=1
def inverse(x,mod):
    return fast_pow_mod(x,mod-2,mod)

#计算快速幂
def fast_pow_mod(x,pow,mod):
    x=x%mod
    pow=pow%mod
    res = 1
    while(pow != 0):
        if ((pow & 1) == 1):
            res = (res % mod * (x%mod))% mod
        pow=pow>>1
        x=((x%mod)*(x%mod))%mod
    return res%mod

#朴素方法求逆元,时间复杂度O(n)
def simple_inv(x,mod):
    for i in range(1,mod):
        if (x*i)%mod==1:
            return i
    return -1

#判断x是否为素数
def is_prime(x):
    if(x<2):
        print("x should be int and bigger than 2")
    if x==2 or x==5:
        return True
    m = int(math.sqrt(x + 0.5))
    if x&1==0 or x&0x111==5:#是偶数或者是5的倍数
        return False
    for i in range(3,m,2):
        if x%i==0:
            return False
    return True

#a*x+b*y=gcd(a,b), 其中返回的x,y分别就是式子中的x,y;q为a和b的最大公约数
def ext_euclid(a, b):
    if b == 0:
        return 1, 0, a
    else:
        x, y, q = ext_euclid(b, a % b)
        # q = gcd(a, b) = gcd(b, a%b)
        x, y = y, (x - (a // b) * y)
        return x, y, q

#根据扩展欧几里得求逆元 ax=1（mod b）
def ext_euclid_inv(a,b):
    res=ext_euclid(a,b)
    x=res[0]
    return x%b