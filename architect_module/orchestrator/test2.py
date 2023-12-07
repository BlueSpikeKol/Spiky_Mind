from architect_module.orchestrator.tree_visualisation import DataVisualizer

#visual = schedule_formation.ProjectSchedule()
#visual.visualize_schedule()
data = {
    "Universe": {
        "metadata": "Level 1",
        "children": {
            "Galaxy Milky Way": {
                "metadata": "Level 2",
                "children": {
                    "Solar System": {
                        "metadata": "Level 3",
                        "children": {
                            "Planet Earth": {
                                "metadata": "Level 4",
                                "children": {
                                    "Continent Africa": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    },
                                    "Continent Asia": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    }
                                }
                            },
                            "Planet Mars": {
                                "metadata": "Level 4",
                                "children": {
                                    "Moon Phobos": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    },
                                    "Moon Deimos": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    }
                                }
                            },
                            "Planet Venus": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    },
                    "Andromeda Galaxy": {
                        "metadata": "Level 3",
                        "children": {
                            "Star System Alpha": {
                                "metadata": "Level 4",
                                "children": {}
                            },
                            "Star System Beta": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    },
                    "Black Hole": {
                        "metadata": "Level 3",
                        "children": {
                            "Event Horizon": {
                                "metadata": "Level 4",
                                "children": {
                                    "Singularity Point": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    },
                                    "Photon Sphere": {
                                        "metadata": "Level 5",
                                        "children": {}
                                    }
                                }
                            },
                            "Accretion Disk": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    }
                }
            },
            "Galaxy Andromeda": {
                "metadata": "Level 2",
                "children": {
                    "Star System Gamma": {
                        "metadata": "Level 3",
                        "children": {}
                    },
                    "Star System Delta": {
                        "metadata": "Level 3",
                        "children": {
                            "Planet Omega": {
                                "metadata": "Level 4",
                                "children": {}
                            },
                            "Planet Sigma": {
                                "metadata": "Level 4",
                                "children": {}
                            }
                        }
                    },
                    "Nebula Epsilon": {
                        "metadata": "Level 3",
                        "children": {}
                    }
                }
            },
            "Intergalactic Space": {
                "metadata": "Level 2",
                "children": {}
            }
        }
    }
}

visualizer = DataVisualizer(data)
visualizer.visualize_data()