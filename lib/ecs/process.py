import boto3
import sys


def print_message(message: str): 
    print(message)
    
    
if __name__ == '__main__':
    args = sys.argv
    if len(args) == 1:
        print('Please say something')
    else:
        for arg in args[1:]:
            print_message(arg)