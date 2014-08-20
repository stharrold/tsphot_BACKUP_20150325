#!/usr/bin/env python
"""Main module for time-series photometry pipeline.

See Also
--------
read_spe : Module for reading SPE files.
utils : Utilities for time-series photometry.

Notes
-----
noinspection : Comments are created by PyCharm to flag permitted code inspection violations.
docstrings : This module's documentation follows the `numpy` doc example [1]_.
TODO : Flag all to-do items with 'TODO:' in the code body (not the docstring) so that they are flagged when using
    an IDE.
'See Also' : Methods describe their relationships to each other within their docstrings under the 'See Also' section.
    All methods should be connected to at least one other method within this module [2]_.

References
----------
.. [1] https://github.com/numpy/numpy/blob/master/doc/example.py
.. [2] http://en.wikipedia.org/wiki/Pipeline_(software)

"""
# TODO: Rename as main.py when 'calibrate' branch is merged with master.

# Forwards compatibility imports.
from __future__ import division, absolute_import, print_function

# Standard library imports.
import os
import json
import pickle
import logging
import argparse
import collections

# External package imports. Grouped procedurally then categorically.

# Internal package imports.
import utils


# noinspection PyShadowingNames
def main(fconfig, rereduce=False, verbose=0):
    """Time-series photometry pipeline.

    Parameters
    ----------
    fconfig : string
        Path to input configuration file as .json.
    rereduce : {False}, bool, optional
        Re-reduce all files. Overwrite previously reduced files. If false, use previously reduced files.
    verbose : {0}, int
        Print 'INFO:' messages to stdout with increasing verbosity.

    Returns
    -------
    None

    Notes
    -----
    Call as top-level script. Example usage:
        $ python main_utils.py --fconfig path/to/config.json -v

    """
    # Read configuration file.
    # Use binary read-write for cross-platform compatibility. Use Python-style indents in the JSON file.
    # TODO: remove verbose variable
    logging.info("Reading configuration file {fconfig}".format(fconfig=fconfig))
    with open(fconfig, 'rb') as fp:
        config_settings = json.load(fp, object_pairs_hook=collections.OrderedDict)
    logging.debug("Configuration file settings: {settings}".format(settings=config_settings))
    # Check configuration file.
    utils.check_config(dobj=config_settings)
    # Create master calibration (calib.)frames.
    # Use binary read-write for cross-platform compatibility. Use Python-style indents in the JSON file.
    # TODO: parallelize
    logging.info("Creating master calibration files.")
    master_ccddata = {}
    master_fpath = config_settings['master']
    # If master calib. frame files already exists, load them. Otherwise initialize master calib. frame as None.
    for imtype in master_fpath:
        mfpath = master_fpath[imtype]
        if (mfpath is not None) and os.path.isfile(mfpath):
            logging.debug("Loading master calibration frame from: {fpath}".format(fpath=mfpath))
            with open(mfpath, 'rb') as fp:
                master_ccddata[imtype] = pickle.load(fp)
        else:
            master_ccddata[imtype] = None
    # If calib. frames exist and if master calib. frames do not yet exist, create master calib. frames.
    # If master calib. frame file is specified, save master calib. frame to file.
    calib_fpath = config_settings['calib']
    for imtype in master_fpath:
        cfpath = calib_fpath[imtype]
        mfpath = master_fpath[imtype]
        if master_ccddata[imtype] is None:
            logging.debug("Creating master calibration frame from: {fpath}".format(fpath=cfpath))
            dobj = utils.spe_to_dict(fpath=cfpath)
            master_ccddata[imtype] = utils.create_master_calib(dobj=dobj)
            if mfpath is not None:
                logging.debug("Writing master calibration frame to: {fpath}".format(fpath=mfpath))
                with open(mfpath, 'wb') as fp:
                    pickle.dump(master_ccddata[imtype], fp)
    # If re-reduce flag given, recreate all master calib. frames.
    # If master calib. frame file is specified, save master calib. frame to file.
    if rereduce:
        for imtype in calib_fpath:
            cfpath = calib_fpath[imtype]
            mfpath = master_fpath[imtype]
            if (cfpath is None) or (not os.path.isfile(cfpath)):
                raise IOError("Calibration frame file does not exist: {fpath}".format(fpath=cfpath))
            logging.debug("Creating master calibration frame from: {fpath}".format(fpath=cfpath))
            dobj = utils.spe_to_dict(fpath=cfpath)
            master_ccddata[imtype] = utils.create_master_calib(dobj=dobj)
            if mfpath is not None:
                logging.debug("Writing master calibration frame to: {fpath}".format(fpath=mfpath))
                with open(mfpath, 'wb') as fp:
                    pickle.dump(master_ccddata[imtype], fp)
    # TODO: resume here
    return None


if __name__ == '__main__':
    defaults = {'fconfig' : 'config.json',
                'flog'    : 'tsphot.log',
                'loglevel': 'INFO'}
    parser = argparse.ArgumentParser(description="Read configuration file and reduce data.")
    parser.add_argument('--fconfig',
                        default=defaults['fconfig'],
                        help=(("Input JSON configuration file.\n" +
                               "Default: {dflt}").format(dflt=defaults['fconfig'])))
    parser.add_argument('--flog',
                        default=defaults['flog'],
                        help=(("Output event log file.\n" +
                               "Default: {dflt}").format(dflt=defaults['flog'])))
    parser.add_argument('--loglevel',
                        default=defaults['loglevel'],
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help=(("Logging level. Determines verbosity threshold for event tracking.\n"+
                               "Default: {dflt}").format(dflt=defaults['loglevel'])))
    parser.add_argument('--rereduce',
                        action='store_true',
                        help=("Re-reduce all files. Overwrite previously reduced files.\n" +
                              "If option omitted, use previously reduced files."))
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help="Print logging messages to stdout.")
    args = parser.parse_args()
    logging.basicConfig(filename='tsphot.log', level=getattr(logging, args.loglevel.upper()))
    logging.info("Arguments: {args}".format(args=args))
    if not os.path.isfile(args.fconfig):
        raise IOError("Configuration file does not exist: {fconfig}".format(fconfig=args.fconfig))
    (fbase, ext) = os.path.splitext(args.fconfig)
    if ext != '.json':
        raise IOError("Configuration file extension is not '.json': {fconfig}".format(fconfig=args.fconfig))
    if args.verbose:
        #TODO: set logging level
        pass
    main(fconfig=args.fconfig, rereduce=args.rereduce, verbose=args.verbose)
