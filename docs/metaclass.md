# Python MetaClass 笔记

在阅读```backtrader```源码的时候发现了一段很有意思的代码
 ```
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, str('temporary_class'), (), {})

class Cerebro(with_metaclass(MetaParams, object)):
    ...
 ```
这段关于```metaclass```的处理引起了我巨大的好奇心，这篇的内容都源于探索这段代码中的点点滴滴。

## Meta Class
这段给之前没有接触过```metaclass```的朋友，简单介绍一下```metaclass```的来源和使用方法。
我想大部分的Python用户都听过一句话：***万物皆对象***。最直观的对象可以直接使用```class```创建，例如下面的一段代码：
 ```
 class A:
    def __init__(self, x):
        self.x = x

 obj_a = A(1)
 ```
 我们知道```obj_a```是一个对象。对Python有一些了解，会知道```obj_a```是由```class A```的```__new__```方法创建的。

 那么对于万物皆对象的Python来说```A```也应该是一个对象，那么是什么可以用来创建对象```A```呢？答案就是```type```。比如我们可以通过下面的代码迅速创建一个类对象：
  ```
  A = type("A", (), {"x":1})
  print(A)
  print(A.__dict__)
  ```
运行这段代码我们可以得到：
 ```
<class '__main__.A'>
{'x': 1, '__module__': '__main__', '__dict__': <attribute '__dict__' of 'A' objects>, '__weakref__': <attribute '__weakref__' of 'A' objects>, '__doc__': None}
 ```
我们发现创建了一个```class A``` 他有一个用户定义的成员```x```

这边我们稍微总结这段内容想要的表达的核心思想：
> [总结]
>
> 在Python中，万物皆对象，除了```type```


## Python2和Python3的兼容性
众所周知，Python是一门面向对象的语言，既然如此，直接使用```type```创建一个类就不是那么符合Python这门语言编程哲学了。因此开发者这个时候，以套娃的方式引入了```metaclass```。用通俗一点的话来说，对于普通的对象，Python使用类里面定义的```__new__```去创建。那么对于类对象，我们就引入一个更加基本的```metaclass```在使用其定义的```__new__```去创建类对象。

### Python2和Python3中的MetaClass
下面我们先以```Python3```为例，通过代码的方式展示整个过程。首先我们通过继承```type```的方式定义个简单的```metaclass```
 ```
class MetaX(type):
    def __new__(cls, cls_name, bases, attrs):
        if "x" not in attrs:
            attrs["x"] = 1
        return super(MetaX, cls).__new__(cls, cls_name, bases, attrs)

class A(object, metaclass=MetaX):
    pass

class B(object, metaclass=MetaX):
    pass

print(A.x)
print(B.x)
 ```

这段代码创建了一个```MetaX```，他的功能就是任何基于```MetaX```创建的类，例如这边的```A```和```B```，他们都会拥有一个成员```x```

在Python3中，我们在声明类时，使用关键字```metaclass```来表明该类构建基于哪个```metaclass```。但是，在Python2中，这段代码是运行不了的，取而代之的实现方式是:
```
class A(object):
    __metaclass__ = MetaX

class B(object):
    __metaclass__ = MetaX
```
这就对代码的兼容性产生了非常严重的影响。对于一个库的开发者来说，他肯定是希望自己的库能够适配越多的Python版本越好，那么这个问题该怎么解决呢？

### 解决兼容性
先直接说结论，```with_metaclass```的神奇之处来了，你会发现下面这段代码即可以在Python3也可以在Python2中运行:
 ```
 class A(with_metaclass(MetaX, object)):
    pass

 class B(with_metaclass(MetaX, object)):
    pass
 ```

这是为什么呢？？？
那么接下来，我们将会深入分析一下这段代码的神奇之处。
首先，如果让我们来做这个兼容性，有一个非常简单直接的想法就是*继承*。第一点一个类对象创建的时候他会寻找```__new__```的实现，那么如果以继承的方式实现，那么就自动可以层层递进地去寻找```__new__```，第二点原因就是继承的用法在Python2和Python3中完全是一样的。那么自然而然，我们就想到通过下面两种方式来声明```A```和```B```
 ```
 class A(type.__new__(MetaX, "temp_class", (), {})):
    pass

 class B(type.__new__(MetaX, "temp_class", (), {})):
    pass
 ```

和我们预想的一样，这段代码是可以在Python2和Python3中正确运行，并且得到我们想要的结果。

那么到了这一步，似乎我们已经解决了版本兼容的问题，而且不需要像```with_metaclass```那样复杂。```with_metaclass```的做法还有必要吗？为了搞清楚这个问题，通过大量尝试，终于发现这两种做法的区别，运行下面这段代码，
 ```
 class A(type.__new__(MetaX, "temp_class", (), {})):
    pass

 class B(with_metaclass(MetaX, object)):
    pass

 print(A.__mro__)
 print(B.__mro__)
 ```
 输出结果为:
 ```
(<class '__main__.A'>, <class 'object'>)
(<class '__main__.B'>, <class '__main__.temp_class'>, <class 'object'>)
 ```
 两种做法，在继承层次上有所区别，```B```很明显继承了```temp_class```，这个确实是符合我们的设计逻辑。但是为什么```A```的```__mro__```中却没有中间的这个```class```。问题的关键就是```metaclass```这个临时类的```__new__```方法中使用了原始的基础```bases```代替了```this_bases```(这边就是```temporary_class```)，一次屏蔽掉了这个临时的中间类。
 
 因此使用```with_metaclass```的方式，确实可以完美地实现在Python2和Python3中的兼容。