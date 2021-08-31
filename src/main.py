from planny import planny
import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('gcal_credentials_json', 
                        help='path of google calendar credentials.json, https://developers.google.com/workspace/guides/create-credentials')
    parser.add_argument('beeminder_json', 
                        help='https://www.beeminder.com/api/v1/auth_token.json, contains username and auth_token')
    parser.add_argument('--debug', action='store_true', help='is debug mode')
    args = parser.parse_args()
    return args

if __name__=='__main__':
    args = parse_args()
    planny.main(args)
