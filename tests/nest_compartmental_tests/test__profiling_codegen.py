# -*- coding: utf-8 -*-
#
# test__profiling_codegen.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.

import os

import pytest

from pynestml.codegeneration.nest_compartmental_code_generator import (
    NESTCompartmentalCodeGenerator,
)
import pynestml.frontend.pynestml_frontend as frontend
from pynestml.frontend.pynestml_frontend import generate_nest_compartmental_target


def _resource_path(name):
    tests_path = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(tests_path, "resources", name)


def test_profiling_codegen_option_validation():
    codegen = NESTCompartmentalCodeGenerator({"nest_version": "v3.4"})

    with pytest.raises(ValueError, match="with_profiling"):
        codegen.set_options({"with_profiling": "yes"})

    with pytest.raises(ValueError, match="freeze_exp_mode"):
        codegen.set_options({"freeze_exp_mode": "freeze_first"})

    with pytest.raises(ValueError, match="single_precision_propagator_exp_mode"):
        codegen.set_options({"single_precision_propagator_exp_mode": "fast"})

    with pytest.raises(ValueError, match="with_detailed_recordables"):
        codegen.set_options({"with_detailed_recordables": "yes"})


def test_profiling_codegen_emits_recordables_and_frozen_exp(tmp_path, monkeypatch):
    monkeypatch.setattr(frontend, "builder_from_target_name", lambda *args, **kwargs: (None, {}))

    baseline_target = tmp_path / "baseline"
    generate_nest_compartmental_target(
        input_path=_resource_path("recordable_inline_test.nestml"),
        target_path=str(baseline_target),
        module_name="profiling_codegen_baseline_module",
        suffix="_nestml",
        logging_level="INFO",
        codegen_opts={"nest_version": "v3.4"},
    )
    baseline_neuroncurrents_h = (
        baseline_target / "cm_neuroncurrents_cm_default_nestml.h"
    ).read_text()
    assert "profile_numstep_ms" not in baseline_neuroncurrents_h
    assert "__frozen_exp_site_0" not in baseline_neuroncurrents_h

    target_path = tmp_path / "target"
    generate_nest_compartmental_target(
        input_path=_resource_path("recordable_inline_test.nestml"),
        target_path=str(target_path),
        module_name="profiling_codegen_module",
        suffix="_nestml",
        logging_level="INFO",
        codegen_opts={
            "nest_version": "v3.4",
            "with_profiling": True,
            "freeze_exp_mode": "freeze_init",
        },
    )

    neuroncurrents_h = (
        target_path / "cm_neuroncurrents_cm_default_nestml.h"
    ).read_text()
    neuroncurrents_cpp = (
        target_path / "cm_neuroncurrents_cm_default_nestml.cpp"
    ).read_text()
    tree_h = (target_path / "cm_tree_cm_default_nestml.h").read_text()
    tree_cpp = (target_path / "cm_tree_cm_default_nestml.cpp").read_text()

    assert "profile_numstep_ms" in neuroncurrents_h
    assert "profile_n_steps" in neuroncurrents_h
    assert "profile_construct_matrix_ms" in tree_cpp
    assert "profile_solve_matrix_ms" in tree_h
    assert "__frozen_exp_site_0" in neuroncurrents_h
    assert "assign(neuron_Na_channel_count" in neuroncurrents_cpp
    assert "Time::get_resolution().get_ms()" in neuroncurrents_cpp


def test_single_precision_propagator_exp_mode_codegen(tmp_path, monkeypatch):
    monkeypatch.setattr(frontend, "builder_from_target_name", lambda *args, **kwargs: (None, {}))

    bounded_target = tmp_path / "bounded"
    generate_nest_compartmental_target(
        input_path=_resource_path("recordable_inline_test.nestml"),
        target_path=str(bounded_target),
        module_name="propagator_bounded_module",
        suffix="_nestml",
        logging_level="INFO",
        codegen_opts={
            "nest_version": "v3.4",
            "fp_precision": "single",
            "single_precision_propagator_exp_mode": "bounded",
        },
    )
    bounded_cpp = (
        bounded_target / "cm_neuroncurrents_cm_default_nestml.cpp"
    ).read_text()
    assert "bounded_propagator_expf" in bounded_cpp

    plain_target = tmp_path / "plain"
    generate_nest_compartmental_target(
        input_path=_resource_path("recordable_inline_test.nestml"),
        target_path=str(plain_target),
        module_name="propagator_plain_module",
        suffix="_nestml",
        logging_level="INFO",
        codegen_opts={
            "nest_version": "v3.4",
            "fp_precision": "single",
            "single_precision_propagator_exp_mode": "plain",
        },
    )
    plain_cpp = (
        plain_target / "cm_neuroncurrents_cm_default_nestml.cpp"
    ).read_text()
    assert "bounded_propagator_expf" not in plain_cpp
    assert "std::expf" in plain_cpp

    fastexp_target = tmp_path / "fastexp"
    generate_nest_compartmental_target(
        input_path=_resource_path("recordable_inline_test.nestml"),
        target_path=str(fastexp_target),
        module_name="propagator_fastexp_module",
        suffix="_nestml",
        logging_level="INFO",
        codegen_opts={
            "nest_version": "v3.4",
            "fp_precision": "single",
            "use_fastexp": True,
            "single_precision_propagator_exp_mode": "plain",
        },
    )
    fastexp_cpp = (
        fastexp_target / "cm_neuroncurrents_cm_default_nestml.cpp"
    ).read_text()
    assert "cm_fast_propagator_exp" in fastexp_cpp
    assert "bounded_propagator_expf" not in fastexp_cpp


def test_detailed_recordables_codegen(tmp_path, monkeypatch):
    monkeypatch.setattr(frontend, "builder_from_target_name", lambda *args, **kwargs: (None, {}))

    target_path = tmp_path / "detailed"
    generate_nest_compartmental_target(
        input_path=_resource_path("recordable_inline_test.nestml"),
        target_path=str(target_path),
        module_name="detailed_recordables_module",
        suffix="_nestml",
        logging_level="INFO",
        codegen_opts={
            "nest_version": "v3.4",
            "with_detailed_recordables": True,
        },
    )

    neuroncurrents_h = (
        target_path / "cm_neuroncurrents_cm_default_nestml.h"
    ).read_text()
    neuroncurrents_cpp = (
        target_path / "cm_neuroncurrents_cm_default_nestml.cpp"
    ).read_text()

    assert "m_inf_Na_recordable" in neuroncurrents_h
    assert "h_inf_Na_recordable" in neuroncurrents_h
    assert "tau_m_Na_recordable" in neuroncurrents_h
    assert "tau_h_Na_recordable" in neuroncurrents_h
    assert "__P__h_Na__h_Na_recordable" in neuroncurrents_h
    assert "__P__m_Na__m_Na_recordable" in neuroncurrents_h
    assert 'Name( std::string("m_inf_Na") + std::to_string(compartment_idx))' in neuroncurrents_cpp
    assert 'Name( std::string("tau_h_Na") + std::to_string(compartment_idx))' in neuroncurrents_cpp
    assert "__P__h_Na__h_Na_recordable[i] = __P__h_Na__h_Na;" in neuroncurrents_cpp
