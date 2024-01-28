(define (domain dc_motor_engineering)
  (:requirements :strips)
  (:predicates
    (materials_selected)
    (dimensions_calculated)
    (design_validated)
    (assembly_completed)
    (testing_done)
    (installed)
    (maintenance_performed)
    (disposed)
  )

  (:action select_materials
    :precondition (not (materials_selected))
    :effect (materials_selected)
  )

  (:action calculate_dimensions
    :precondition (materials_selected)
    :effect (dimensions_calculated)
  )

  (:action validate_design
    :precondition (dimensions_calculated)
    :effect (design_validated)
  )

  (:action assemble
    :precondition (design_validated)
    :effect (assembly_completed)
  )

  (:action test
    :precondition (assembly_completed)
    :effect (testing_done)
  )

  (:action install
    :precondition (testing_done)
    :effect (installed)
  )

  (:action perform_maintenance
    :precondition (installed)
    :effect (maintenance_performed)
  )

  (:action dispose
    :precondition (maintenance_performed)
    :effect (disposed)
  )
)
