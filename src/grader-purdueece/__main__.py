import argparse
import csv
import json
import logging
import os
import re
import subprocess
import sys


def main(args):
    # arg parsing
    parser = argparse.ArgumentParser('grader')
    parser.add_argument(
        'path',
        default='template',
        help='path of the module to grade',
    )
    parser.add_argument(
        '--submission',
        default='assignment',
        help='submission name to grade',
    )
    parser.add_argument(
        '--tests',
        default='grader',
        help='path of tests to run',
    )
    parser.add_argument(
        '--test-pattern',
        default='test*.py',
        help='test name pattern to match',
    )
    parser.add_argument(
        '--output',
        help='output file for scores',
    )
    parser.add_argument(
        '--log',
        help='log file to use',
    )
    parser.add_argument(
        '--config',
        help='config file to use',
        default=f'grader/config.json',
    )
    args = parser.parse_args(args)

    # setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        handlers=[logging.StreamHandler(open(args.log, 'w+') if args.log else sys.stdout)]
    )
    logging.debug(f'Args:\n{args}\n\n')
    
    # load configs
    try:
        with open(args.config) as f:
            conf = json.load(f)
    except:
        conf = {}
    logging.debug(f'Config:\n{json.dumps(conf, indent=4)}\n\n')
    rconf: dict = conf.get('submissions', {}).get(args.submission, {})
    logging.debug(f'Submission Config:\n{json.dumps(rconf, indent=4)}\n\n')
    
    # setup outputs
    scores = { 'name': rconf.get('name', args.submission) }

    # run tests
    cwd = os.getcwd()
    try:
        os.chdir(args.path)
        proc = subprocess.run(f'python3 -m unittest discover -vs {cwd}/{args.tests} -p {args.test_pattern}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, check=True, encoding='utf-8')
    except Exception as e:
        logging.exception(f'Exception while running tests: {e}\n')
        logging.exception(f'Running with empty module\n')
        os.chdir(f'{cwd}/template')
        proc = subprocess.run(f'python3 -m unittest discover -vs {cwd}/{args.tests} -p {args.test_pattern}', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, encoding='utf-8')
    finally:
        logging.info(proc.stdout)
        os.chdir(cwd)
        
    # check output
    for testName, result in re.findall(r'(.*) \.\.\. (.*)', proc.stdout):
        tconf: dict = conf.get('tests', {}).get(testName, {})
        tlabel = tconf.get('name', testName)
        weight = tconf.get('weight', 1)
        scores[tlabel] = 1 * weight if result == 'ok' else 0

    # results
    with open(args.output, 'w') if args.output else sys.stdout as f:
        writer = csv.DictWriter(f=f, fieldnames=scores.keys())
        writer.writeheader()
        writer.writerow(scores)

if __name__ == "__main__":
    main(sys.argv[1:])
