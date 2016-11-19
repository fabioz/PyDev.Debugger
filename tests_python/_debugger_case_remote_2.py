if __name__ == '__main__':
    print('Run as main: %s' % (__file__,))
    import sys;sys.path.append(r'X:\pydev\plugins\org.python.pydev\pysrc')
    import pydevd;pydevd.settrace()
    print('finish')