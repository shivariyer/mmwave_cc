

def prettyprint_args(ns):
    import os
    
    print(os.linesep + 'Input arguments -- ')
    
    for k,v in ns.__dict__.items():
        print('{}: {}'.format(k,v))

    print()
    return


