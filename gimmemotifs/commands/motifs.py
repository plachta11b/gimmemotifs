#!/usr/bin/python -W ignore
# Copyright (c) 2009-2016 Simon van Heeringen <simon.vanheeringen@gmail.com>
#
# This module is free software. You can redistribute it and/or modify it under
# the terms of the MIT License, see the file COPYING included with this
# distribution.
"""Command line function 'roc'."""
from __future__ import print_function
import os
import sys
import shutil
import logging
from tempfile import NamedTemporaryFile

import numpy as np

from gimmemotifs.motif import read_motifs
from gimmemotifs.stats import calc_stats_iterator
from gimmemotifs.denovo import gimme_motifs
from gimmemotifs.background import create_background_file
from gimmemotifs.comparison import MotifComparer
from gimmemotifs.report import roc_html_report
from gimmemotifs.utils import determine_file_type, narrowpeak_to_bed

logger = logging.getLogger("gimme.motifs")


def motifs(args):
    """ Calculate ROC_AUC and other metrics and optionally plot ROC curve."""
    if args.outdir:
        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

    bgfile = None
    bg = args.background
    if bg is None:
        bg = "gc"

    if os.path.isfile(bg):
        bgfile = bg
        bg = "custom"
    else:
        # create background if not provided
        bgfile = os.path.join(args.outdir, "generated_background.{}.fa".format(bg))
        size = args.size
        if size <= 0:
            size = None
        logger.info("creating background (matched GC%)")
        create_background_file(
            bgfile,
            bg,
            fmt="fasta",
            genome=args.genome,
            inputfile=args.sample,
            size=size,
            number=10000,
        )

    pfmfile = args.pfmfile

    motifs = read_motifs(pfmfile, fmt="pwm")
    if args.denovo:
        print(args.genome)
        gimme_motifs(
            args.sample,
            args.outdir,
            params={
                "tools": args.tools,
                "analysis": args.analysis,
                "background": bg,
                "custom_background": bgfile,
                "genome": args.genome,
                "size": args.size,
            },
        )
        denovo = read_motifs(os.path.join(args.outdir, "gimme.denovo.pfm"))
        mc = MotifComparer()
        result = mc.get_closest_match(denovo, dbmotifs=pfmfile, metric="seqcor")
        new_map_file = os.path.join(args.outdir, "combined.motif2factors.txt")
        base = os.path.splitext(pfmfile)[0]
        map_file = base + ".motif2factors.txt"
        if os.path.exists(map_file):
            shutil.copyfile(map_file, new_map_file)

        motifs += denovo
        pfmfile = os.path.join(args.outdir, "combined.pfm")
        with open(pfmfile, "w") as f:
            for m in motifs:
                print(m.to_pwm(), file=f)

        with open(new_map_file, "a") as f:
            for m in denovo:
                print(
                    "{}\t{}\t{}\t{}".format(m.id, "de novo", "GimmeMotifs", "Y"), file=f
                )
                for copy_m in motifs:
                    if copy_m.id == result[m.id][0]:
                        for factor in copy_m.factors["direct"]:
                            print(
                                "{}\t{}\t{}\t{}".format(
                                    m.id, factor, "inferred (GimmeMotifs)", "N"
                                ),
                                file=f,
                            )

                        break
    else:
        logger.info("skipping de novo")

    stats = [
        "phyper_at_fpr",
        "roc_auc",
        "pr_auc",
        "enr_at_fpr",
        "recall_at_fdr",
        "roc_values",
        "matches_at_fpr",
    ]

    f_out = sys.stdout
    if args.outdir:
        f_out = open(args.outdir + "/gimme.roc.report.txt", "w")

    # Print the metrics
    f_out.write(
        "Motif\t# matches\t# matches background\tP-value\tlog10 P-value\tROC AUC\tPR AUC\tEnr. at 1% FPR\tRecall at 10% FDR\n"
    )

    logger.info("calculating stats")
    ftype = determine_file_type(args.sample)
    sample = args.sample
    if ftype == "narrowpeak":
        f = NamedTemporaryFile()
        logger.debug("Using %s as temporary BED file".format(f.name))
        narrowpeak_to_bed(args.sample, f.name, size=args.size)
        sample = f.name

    for motif_stats in calc_stats_iterator(
        motifs,
        sample,
        bgfile,
        stats=stats,
        genome=args.genome,
        ncpus=args.ncpus,
        zscore=args.zscore,
        gc=args.gc,
    ):

        for motif in motifs:
            if str(motif) in motif_stats:
                log_pvalue = np.inf
                if motif_stats[str(motif)]["phyper_at_fpr"] > 0:
                    log_pvalue = -np.log10(motif_stats[str(motif)]["phyper_at_fpr"])
                f_out.write(
                    "{}\t{:d}\t{:d}\t{:.2e}\t{:.3f}\t{:.3f}\t{:.3f}\t{:.2f}\t{:0.4f}\n".format(
                        motif.id,
                        motif_stats[str(motif)]["matches_at_fpr"][0],
                        motif_stats[str(motif)]["matches_at_fpr"][1],
                        motif_stats[str(motif)]["phyper_at_fpr"],
                        log_pvalue,
                        motif_stats[str(motif)]["roc_auc"],
                        motif_stats[str(motif)]["pr_auc"],
                        motif_stats[str(motif)]["enr_at_fpr"],
                        motif_stats[str(motif)]["recall_at_fdr"],
                    )
                )
    f_out.close()

    if args.report:
        logger.info("creating statistics report")
        if args.outdir:
            roc_html_report(
                args.outdir, args.outdir + "/gimme.roc.report.txt", pfmfile, 0.01
            )
