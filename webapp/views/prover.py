from json import JSONDecoder, JSONEncoder
import logging
import telnetlib
from uuid import uuid4

from flask import (
    Module,
    url_for,
    render_template,
    request,
    session,
    )

prover = Module(__name__)


def readscript(script):
    '''Chew up blank lines'''
    return [x for x in script.splitlines() if not x == '']


def formatscript(script, slice):
    commandlist = readscript(script)
    processed = '\\n'.join(commandlist[:slice + 1])
    unprocessed = '\\n'.join(commandlist[slice + 2:])
    return processed, unprocessed, commandlist


def ping_coqd():
    pass


@prover.route('/prover', methods=['GET', 'POST'])
def editor():
    proofst = None
    unprocessed = "(* Begin Your Proof Here *)"
    lineno = 0

    ping_coqd()

    if request.method == 'POST':
        if not session.get('id'):
            session['id'] = uuid4()

        if request.form.get('clear'):
            command = 'quit'
            proofscript = request.form.get('proofscript')
            processed, unprocessed, commandlist = formatscript(proofscript, 0)
            processed = None

        elif request.form.get('undo'):
            lineno = int(request.form.get('line')) - 1
            proofscript = request.form.get('proofscript')
            processed, unprocessed, commandlist = formatscript(proofscript,
                                                               lineno)
            command = 'Undo.'

        else:
            lineno = int(request.form.get('line')) + 1
            proofscript = request.form.get('proofscript')
            processed, unprocessed, commandlist = formatscript(proofscript,
                                                  lineno)
            command = commandlist[lineno]
            logging.debug('Sending %d : %s', lineno, command)

        # here is where we'll pass it to coqd
        if command:
            try:
                tn = telnetlib.Telnet('localhost', 8001)
                tn.write(JSONEncoder().encode(dict(userid=str(session['id']),
                                               command=command)))

                proofst = JSONDecoder().decode(tn.read_all())
                proofst = proofst.get('response', None)
            except Exception:
                logging.error("Connection to coqd failed")

        return render_template('prover.html',
                               prover_url=url_for('editor'),
                               processed=processed,
                               unprocessed=unprocessed,
                               proofst=proofst,
                               lineno=lineno)
    else:
        return render_template('prover.html',
                               prover_url=url_for('editor'),
                               proofst=proofst,
                               processed=None,
                               unprocessed=unprocessed,
                               lineno=lineno)