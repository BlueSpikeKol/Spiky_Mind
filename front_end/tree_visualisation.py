from PyQt6.QtWidgets import QApplication, QGraphicsScene
from PyQt6.QtCore import Qt
import sys

from front_end.pyqt_scene_objects.pyqt_scene_view import TreeSceneView
from front_end.pyqt_scene_objects.pyqt_objects import NodeItem, EdgeItem

class DataVisualizer:
    def __init__(self, data):
        self.data = data
        self.app = QApplication(sys.argv)
        self.scene = QGraphicsScene()
        self.view = TreeSceneView(self.scene, self)
        self.loaded_nodes = {}  # Dictionary to store NodeItem objects
        self.create_nodes(data)  # Create NodeItem objects from the data
        self.updateSceneRect()
        self.edges_are_cleaned = False
        self.nodes_in_view = set()
        self.nodes_not_in_view = set()
        self.last_viewport_rect = None
        self.deleted_edges = []  # List to track deleted edges
        self.edges_in_scene = set()
        self.edges_not_in_scene = set()

    def check_if_node_is_centered(self, node):
        if not node.children_nodes:
            print(f"Node '{node.label}' has no children to center with.")
            return

        child_center = self.calculate_children_center_x(node)
        middle_node_x = node.stored_pos.x() + node.boundingRect().width() / 2

        # Check if the node is almost centered with a tolerance of 1 unit
        is_almost_centered = abs(middle_node_x - child_center) < 1
        if is_almost_centered:
            print(f"Node '{node.label}' is centered with its children.")
        else:
            difference = abs(middle_node_x - child_center)
            print(f"Node '{node.label}' is not centered. Difference: {difference}")

    def refreshView(self):
        """Refresh the graphics view."""
        self.view.update()  # Assuming the QGraphicsView instance is stored in self.view
        QApplication.processEvents()

    def updateSceneRect(self):
        # Calculate the bounding box of all nodes
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        border_padding = 200  # Extra space around the nodes

        for node in self.loaded_nodes.values():
            rect = node.sceneBoundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())

        # Set scene dimensions based on nodes' positions
        scene_width = max_x - min_x + 2 * border_padding
        scene_height = max_y - min_y + 2 * border_padding
        self.scene.setSceneRect(min_x - border_padding, min_y - border_padding, scene_width, scene_height)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def update_all_edges(self):
        for node_item in self.loaded_nodes.values():
            node_item.updateEdges()

    def cleanup_edges(self):
        edges_to_delete = []

        for node_item in self.loaded_nodes.values():
            for edge in node_item.edges.copy():  # Use a copy to safely modify the list during iteration
                # Check conditions for the end_item of the edge
                is_end_item_in_view = edge.end_item in self.nodes_in_view
                is_end_item_not_in_view = edge.end_item in self.nodes_not_in_view
                is_end_item_in_scene = edge.end_item.scene() is not None
                is_end_item_loaded = edge.end_item in self.loaded_nodes.values()

                # If all conditions are false for the end_item, mark the edge for deletion
                if not any([is_end_item_in_view, is_end_item_not_in_view, is_end_item_in_scene, is_end_item_loaded]):
                    edges_to_delete.append(edge)

        print("edges deleted at once: " + str(len(edges_to_delete)))
        # Delete the marked edges using self.scene and remove references
        for edge in edges_to_delete:
            if edge.scene():
                self.scene.removeItem(edge)
            # Remove references from the connected nodes
            if edge.start_item and edge in edge.start_item.edges:
                edge.start_item.edges.remove(edge)
            if edge.end_item and edge in edge.end_item.edges:
                edge.end_item.edges.remove(edge)
            # Remove the edge from the deleted_edges list if it's there
            if edge in self.deleted_edges:
                self.deleted_edges.remove(edge)
            # Finally, delete the edge object
            del edge

    def update_visible_nodes(self, action):
        visible_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
        self._load_nodes(visible_rect, action)
        if not self.edges_are_cleaned:
            self.cleanup_edges()
            self.edges_are_cleaned = True

    def on_node_position_changed(self, new_pos):
        # This method will be called whenever a node's position changes
        print(f"Node position changed to {new_pos}")

    def create_nodes(self, data, parent=None):
        if not hasattr(self, 'name_counter'):
            self.name_counter = {}  # Initialize a counter for node names

        for original_key, value in data.items():
            key = original_key
            # Check if the key already exists and modify it if necessary
            while key in self.loaded_nodes:
                self.name_counter[original_key] = self.name_counter.get(original_key, 1) + 1
                key = f"{original_key}_{self.name_counter[original_key]}"

            # Handle cases where value is None
            if value is None:
                metadata = ''
                children = {}
            else:
                metadata = value.get('metadata', '')
                children = value.get('children', {})

            node_item = NodeItem(key, metadata, parent, visualizer=self)
            self.loaded_nodes[key] = node_item

            node_item.signals.positionChanged.connect(self.on_node_position_changed)

            # Add the node to the scene and check if it's added correctly
            self.scene.addItem(node_item)
            if node_item.scene() != self.scene:
                print(f"Failed to add node '{key}' to the scene.")

            if parent:
                edge = EdgeItem(parent, node_item)
                parent.edges.append(edge)
                node_item.edges.append(edge)

                # Add the edge to the scene and check if it's added correctly
                self.scene.addItem(edge)
                if edge.scene() != self.scene:
                    print(f"Failed to add edge between '{parent.label}' and '{node_item.label}' to the scene.")

                parent.addChild(node_item)
                for sibling in parent.children_nodes:
                    if sibling is not node_item:
                        sibling.addSibling(node_item)
                        node_item.addSibling(sibling)

            # Recursively create nodes for children
            self.create_nodes(children, node_item)

    def initial_load(self):

        # Build the tree structure as a list of levels with sibling groups
        self.build_tree_levels()
        # Position nodes based on the tree structure
        self.position_nodes()
        # Update the scene boundary to encompass all nodes
        self.updateSceneRect()

    def build_tree_levels(self, depth=0, tree_levels=None, parent=None):
        if tree_levels is None:
            tree_levels = []

        while len(tree_levels) <= depth:
            tree_levels.append([])

        if parent is None:
            # Find and process root nodes (nodes without a parent)
            for node_item in self.loaded_nodes.values():
                if node_item.parent_node is None:
                    self.process_node_for_tree_levels(node_item, depth, tree_levels)
        else:
            # Process children of the given parent
            for child in parent.children_nodes:
                self.process_node_for_tree_levels(child, depth, tree_levels)

        self.tree_levels = tree_levels

    def process_node_for_tree_levels(self, node_item, depth, tree_levels):
        # Find or create the sibling group for this node
        parent_key = node_item.parent_node.label if node_item.parent_node else 'root'
        sibling_group = next((group for group in tree_levels[depth] if group['parent'] == parent_key), None)
        if sibling_group is None:
            sibling_group = {'parent': parent_key, 'nodes': [], 'total_width': 0}
            tree_levels[depth].append(sibling_group)

        # Add the node to the sibling group
        sibling_group['nodes'].append(node_item)
        node_item_width = node_item.boundingRect().width()
        sibling_group['total_width'] += node_item_width

        # Recursively process children
        if node_item.children_nodes:
            self.build_tree_levels(depth + 1, tree_levels, node_item)

    def position_nodes(self):
        """
        Position nodes based on their level in the tree and adjust to prevent overlaps.
        Each level is separated by 100 units on the y-axis.
        """
        self.position_nodes_flat()
        # print(self.loaded_nodes['Singularity Point'].stored_pos)
        self.center_children_below_parents()
        # print(self.loaded_nodes['Singularity Point'].stored_pos)
        self.adjust_positions_to_prevent_overlaps()
        # print('test')
        # print(self.loaded_nodes['Star System Alpha'].stored_pos)
        # print(self.loaded_nodes['Planet Venus'].stored_pos)
        self.recenter_parents_above_children()
        # print('test')
        # print(self.loaded_nodes['Star System Alpha'].stored_pos)
        # print(self.loaded_nodes['Planet Venus'].stored_pos)

    def position_nodes_flat(self):
        """
        Position nodes in a flat structure based on their level, only adjusting the y-axis.
        """
        y_spacing = 400  # Vertical spacing between levels

        for level_index, level in enumerate(self.tree_levels):
            y_position = level_index * y_spacing

            for sibling_group in level:
                for node in sibling_group['nodes']:
                    if node.label == "Documentation":
                        print()
                    # Keep the current x position, only update the y position
                    current_x = node.stored_pos.x()
                    node.setStoredPos(current_x, y_position)

    def center_children_below_parents(self):
        """
        Center each group of sibling nodes below their parent node.
        """
        for level in self.tree_levels:
            for sibling_group in level:
                for node in sibling_group['nodes']:
                    if node.children_nodes:
                        self.center_children_group_below_parent(node)

    def center_children_group_below_parent(self, parent_node):
        """
        Center a group of sibling nodes (children of the same parent) below their parent node.
        """
        if not parent_node.children_nodes:
            return

        # Ensure no overlapping among children
        self.ensure_no_children_overlap(parent_node)

        # Calculate the leftmost and rightmost points of the children
        leftmost_x = min(child.stored_pos.x() for child in parent_node.children_nodes)
        rightmost_x = max(child.stored_pos.x() + child.boundingRect().width() for child in parent_node.children_nodes)
        children_center_x = (leftmost_x + rightmost_x) / 2

        # Calculate the center of the parent
        parent_center_x = parent_node.stored_pos.x() + parent_node.boundingRect().width() / 2

        # Shift all children to align centers
        shift_amount = parent_center_x - children_center_x
        for child in parent_node.children_nodes:
            child.setStoredPos(child.stored_pos.x() + shift_amount, child.stored_pos.y())



    def ensure_no_children_overlap(self, parent_node):
        """
        Adjust positions of children nodes to ensure no overlap.
        """
        sorted_children = sorted(parent_node.children_nodes, key=lambda n: n.stored_pos.x())
        for i in range(len(sorted_children) - 1):
            current_child = sorted_children[i]
            next_child = sorted_children[i + 1]
            right_edge_current = current_child.stored_pos.x() + current_child.boundingRect().width()
            if right_edge_current > next_child.stored_pos.x():
                # Calculate overlap and adjust position
                overlap = right_edge_current - next_child.stored_pos.x()
                next_child.setStoredPos(next_child.stored_pos.x() + overlap, next_child.stored_pos.y())



    def adjust_positions_to_prevent_overlaps(self):
        cushion = 0  # Additional space between nodes

        for level_index, level in enumerate(self.tree_levels):
            for i in range(len(level) - 1):
                current_group = level[i]
                next_group = level[i + 1]

                if not current_group['nodes'] or not next_group['nodes']:
                    continue

                rightmost_node = current_group['nodes'][-1]
                leftmost_node_next_group = next_group['nodes'][0]

                right_edge = rightmost_node.stored_pos.x() + rightmost_node.boundingRect().width()
                left_edge_next = leftmost_node_next_group.stored_pos.x()

                if right_edge + cushion > left_edge_next:
                    shift_amount = right_edge + cushion - left_edge_next
                    self.shift_sibling_group_and_subtrees(leftmost_node_next_group.parent_node, shift_amount)

    def shift_sibling_group_and_subtrees(self, parent_node, shift_amount):
        """
        Shift an entire sibling group (all children of a common parent) and their subtrees by a specified amount.
        """
        for child in parent_node.children_nodes:
            self.shift_node_and_subtree(child, shift_amount)

    def shift_node_and_subtree(self, node, shift_amount):
        """
        Recursively shift a node and its descendants.
        """
        node.setStoredPos(node.stored_pos.x() + shift_amount, node.stored_pos.y())
        for child in node.children_nodes:
            self.shift_node_and_subtree(child, shift_amount)

    def recenter_parents_above_children(self):
        for level in reversed(self.tree_levels):
            for sibling_group in level:
                if sibling_group['nodes']:
                    parent_node = sibling_group['nodes'][0].parent_node
                    if parent_node:
                        # if parent_node.label == 'Manufacturing' or parent_node.label == 'Fabrication' or parent_node.label == 'Assembling Components':
                        #     break
                        self.center_parent_above_sibling_group(parent_node, sibling_group['nodes'])

    def center_parent_above_sibling_group(self, parent_node, sibling_nodes):
        if not sibling_nodes:
            return

        while True:
            # Center the parent node above its children
            shift_amount = self.calculate_shift_to_center_parent(parent_node)
            # -100440.0
            if parent_node.label == 'Attaching Components' or parent_node.label == 'Motor Selection': # 18600.0
                pos = parent_node.stored_pos
                print()
            parent_node.setStoredPos(parent_node.stored_pos.x() + shift_amount, parent_node.stored_pos.y())

            # If the shift amount is not zero, adjust sibling positions
            if shift_amount != 0:
                self.shift_siblings_and_subtrees(parent_node, shift_amount)
            else:
                # Resolve overlaps with the left sibling
                self.resolve_sibling_overlaps(parent_node)

                # Recalculate shift amount to check if further adjustment is needed
                new_shift_amount = self.calculate_shift_to_center_parent(parent_node)
                if new_shift_amount == 0:
                    break

    def calculate_shift_to_center_parent(self, parent_node):
        if not parent_node.children_nodes:
            return 0

        children_leftmost_x = min(child.stored_pos.x() for child in parent_node.children_nodes)
        children_rightmost_x = max(
            child.stored_pos.x() + child.boundingRect().width() for child in parent_node.children_nodes)
        children_center_x = (children_leftmost_x + children_rightmost_x) / 2
        parent_center_x = parent_node.stored_pos.x() + parent_node.boundingRect().width() / 2
        return children_center_x - parent_center_x

    def shift_siblings_and_subtrees(self, parent_node, shift_amount):
        level_index = self.find_level_index(parent_node)
        if level_index is None:
            return

        all_nodes_at_level = [node for group in self.tree_levels[level_index] for node in group['nodes']]
        parent_index = all_nodes_at_level.index(parent_node)

        # Apply shifting to all nodes at the level
        for node in all_nodes_at_level:
            print()
            if node != parent_node:
                if node.label == 'Attaching Components' and shift_amount < 0:
                    print()
                if node.label == 'Motor Selection':
                    print()
                node_index = all_nodes_at_level.index(node)
                self.shift_node_and_subtree_if_needed(node, shift_amount, parent_index, node_index)




    def shift_node_and_subtree_if_needed(self, node, shift_amount, parent_index, node_index):
        # Determine if the node is supposed to be to the left or right of the parent
        is_supposed_to_be_left = node_index < parent_index
        is_supposed_to_be_right = node_index > parent_index

        # Calculate the center of the children nodes before shifting
        child_center = self.calculate_children_center_x(node)


        # Apply the shift only if it aligns with the node's supposed position
        if (shift_amount > 0 and is_supposed_to_be_right) or (shift_amount < 0 and is_supposed_to_be_left):
            original_middle_node_x = node.stored_pos.x() + node.boundingRect().width() / 2
            new_x = node.stored_pos.x() + shift_amount
            node.setStoredPos(new_x, node.stored_pos.y())
            if node.label == "Magnetic Field Analysis_2":
                node_ps = node.stored_pos
                print()
            if node.label == "Research motor specifications":
                node_ps = node.stored_pos
                print()
            #self.resolve_sibling_overlaps(node)

            # Determine if the node has overshot the center of its children
            overshot, overshoot_amount = self.check_and_calculate_overshoot(node, original_middle_node_x, child_center,
                                                                            shift_amount)

            # Apply the adjusted shift to the children
            if not overshot and node.label == 'Motor Selection':
                print()
            if overshot:
                for child in node.children_nodes:
                    self.shift_node_and_subtree(child, overshoot_amount if shift_amount > 0 else -overshoot_amount)
            if node.label == "Electromagnetic Design" or node.label == "Simulation":
                print()
                for test in self.loaded_nodes.values():
                    if test.label == "Motor Performance Testing":
                        motor_testing_node = test.stored_pos
                        print()
                    elif test.label == "Performance Analysis and Optimization":
                        performance_analysis_node = test.stored_pos
                        print()


    def check_and_calculate_overshoot(self, node, original_middle_node_x, child_center, shift_amount):
        overshot = False
        overshoot_amount = 0
        if node.children_nodes:  # Check if the node has children
            # Check for overshoot with a tolerance of 1 unit
            is_almost_centered = abs(original_middle_node_x - child_center) < 1
            new_x = node.stored_pos.x() + node.boundingRect().width() / 2
            overshot = (
                    (shift_amount > 0 and (
                                is_almost_centered or original_middle_node_x < child_center) and new_x > child_center) or
                    (shift_amount < 0 and (
                                is_almost_centered or original_middle_node_x > child_center) and new_x < child_center)
            )
            if overshot:
                # Calculate the amount of overshoot
                overshoot_amount = abs(new_x - child_center) if not is_almost_centered else abs(shift_amount)
        return overshot, overshoot_amount

    def resolve_sibling_overlaps(self, node):
        left_sibling, _ = self.findImmediateSiblings(node)
        if left_sibling:
            rightmost_child_of_left_sibling = max(left_sibling.children_nodes,
                                                  key=lambda n: n.stored_pos.x() + n.boundingRect().width(),
                                                  default=None)
            leftmost_child_of_node = min(node.children_nodes, key=lambda n: n.stored_pos.x(), default=None)
            if rightmost_child_of_left_sibling and leftmost_child_of_node and rightmost_child_of_left_sibling.stored_pos.x() + rightmost_child_of_left_sibling.boundingRect().width() > leftmost_child_of_node.stored_pos.x():
                # Calculate overlap and shift node's children
                overlap = rightmost_child_of_left_sibling.stored_pos.x() + rightmost_child_of_left_sibling.boundingRect().width() - leftmost_child_of_node.stored_pos.x()
                for child in node.children_nodes:
                    child.setStoredPos(child.stored_pos.x() + overlap, child.stored_pos.y())

    def findImmediateSiblings(self, node):
        if not node.parent_node:
            return None, None  # No siblings if there's no parent

        all_nodes_at_level = self.get_all_nodes_at_same_level(node)
        node_index = all_nodes_at_level.index(node)

        # Find the nearest node to the left with children
        left_sibling = None
        for i in range(node_index - 1, -1, -1):
            if all_nodes_at_level[i].children_nodes:
                left_sibling = all_nodes_at_level[i]
                break

        # Find the nearest node to the right with children
        right_sibling = None
        for i in range(node_index + 1, len(all_nodes_at_level)):
            if all_nodes_at_level[i].children_nodes:
                right_sibling = all_nodes_at_level[i]
                break

        return left_sibling, right_sibling

    def get_all_nodes_at_same_level(self, node):
        # Assuming you have a way to determine the level of a node
        level_index = self.find_level_index(node)
        if level_index is not None:
            # Flatten all sibling groups at this level into a single list
            return [n for group in self.tree_levels[level_index] for n in group['nodes']]
        return []

    def calculate_children_center_x(self, node):
        if not node.children_nodes:
            # Return the node's own x-position if it has no children
            return node.stored_pos.x()

        children_leftmost_x = min(child.stored_pos.x() for child in node.children_nodes)
        children_rightmost_x = max(child.stored_pos.x() + child.boundingRect().width() for child in node.children_nodes)
        return (children_leftmost_x + children_rightmost_x) / 2

    def find_level_index(self, node):
        for level_index, level in enumerate(self.tree_levels):
            for sibling_group in level:
                if node in sibling_group['nodes']:
                    return level_index
        return None

    def visualize_data(self):
        if isinstance(self.data, dict):
            self.initial_load()
            self.view.show()
            self.update_all_edges()
            sys.exit(self.app.exec())
        else:
            print("Invalid data format for visualization")

    def _load_nodes(self, visible_rect, action):
        for node_id, node_item in self.loaded_nodes.items():
            if action == "zoom_in" and node_item in self.nodes_in_view:
                self.process_node(node_item, visible_rect, remove_only=True)
            elif action == "zoom_out" and node_item in self.nodes_not_in_view:
                self.process_node(node_item, visible_rect, add_only=True)
            elif action == "pan":
                self.process_node(node_item, visible_rect)

        self.update_edge_visibility(action=action)

    def update_edge_visibility(self, action):
        if action == "zoom_in":
            # Hide edges if both connected nodes are not visible
            for edge in self.edges_in_scene:
                if not (edge.start_item.isVisible() and edge.end_item.isVisible()):
                    edge.setVisible(False)
                    self.edges_not_in_scene.add(edge)
                    self.edges_in_scene.discard(edge)

        elif action == "zoom_out":
            # Show edges if either of the connected nodes is visible
            for edge in self.edges_not_in_scene:
                if edge.start_item.isVisible() or edge.end_item.isVisible():
                    edge.setVisible(True)
                    self.edges_in_scene.add(edge)
                    self.edges_not_in_scene.discard(edge)

        else:  # action == "pan"
            # Update visibility based on connected nodes' visibility
            for edge in self.edges_in_scene.union(self.edges_not_in_scene):
                edge_visible = edge.start_item.isVisible() or edge.end_item.isVisible()
                edge.setVisible(edge_visible)
                if edge_visible:
                    self.edges_in_scene.add(edge)
                    self.edges_not_in_scene.discard(edge)
                else:
                    self.edges_not_in_scene.add(edge)
                    self.edges_in_scene.discard(edge)

    def process_node(self, node_item, visible_rect, add_only=False, remove_only=False):
        # Ensure the root node and its children are in the scene

        if node_item:
            node_rect = node_item.sceneBoundingRect()

            if node_rect.intersects(visible_rect):
                if not remove_only and node_item not in self.nodes_in_view:
                    node_item.setVisible(True)
                    self.nodes_in_view.add(node_item)
                    self.nodes_not_in_view.discard(node_item)
            else:
                if not add_only and node_item in self.nodes_in_view:
                    node_item.setVisible(False)
                    self.nodes_not_in_view.add(node_item)
                    self.nodes_in_view.discard(node_item)

    def add_node_to_scene(self, node_item, visible_rect):
        # Add the node to the scene
        self.scene.customAddItem(node_item)
        if node_item not in self.nodes_in_view:
            self.nodes_in_view.add(node_item)
        self.nodes_not_in_view.discard(node_item)

        # Check and remove direct children that are not in the visible area
        for child in node_item.childItems():
            if child in self.nodes_in_view and not child.sceneBoundingRect().intersects(visible_rect):
                self.scene.customRemoveItem(child)
                if child not in self.nodes_not_in_view:
                    self.nodes_not_in_view.add(child)

    def remove_node_from_scene(self, node_item, visible_rect):
        if isinstance(node_item, NodeItem):
            # Remove the node from the scene
            self.scene.customRemoveItem(node_item)
            if node_item not in self.nodes_not_in_view:
                self.nodes_not_in_view.add(node_item)
            self.nodes_in_view.discard(node_item)

            # Re-add edges if one of the connected nodes is still in view
            for edge in node_item.edges:
                other_node = edge.end_item if edge.start_item == node_item else edge.start_item
                if other_node in self.nodes_in_view and edge not in self.nodes_in_view:
                    self.scene.customAddItem(edge)
                    if edge not in self.nodes_in_view:
                        self.nodes_in_view.add(edge)

            # Handle children independently
            for child in node_item.childItems():
                if child not in self.nodes_in_view and child.sceneBoundingRect().intersects(visible_rect):
                    self.scene.customAddItem(child)
                    if child not in self.nodes_in_view:
                        self.nodes_in_view.add(child)
                    self.nodes_not_in_view.discard(child)


if __name__ == "__main__":
    # Sample data for testing
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
                                        },

                                        "testa": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testb": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testc": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testd": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "teste": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testf": {
                                            "metadata": "Level 4",
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
                                },

                                "testt": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testfdsa": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testgsda": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testsadv": {
                                    "metadata": "Level 4",
                                    "children": {
                                        "testvmeb": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testesfa": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        }
                                        ,

                                        "testvas": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        }
                                        ,

                                        "testvaiknb": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        }
                                        ,

                                        "testpajfv": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        }
                                        ,

                                        "testuyvfd": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testhrbe": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        }
                                    }
                                },

                                "testbcvs": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testdav": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testgdsa": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testgrpo": {
                                    "metadata": "Level 4",
                                    "children": {}
                                },

                                "testsagj": {
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
                                        },
                                        "Gravitational Lens 1": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Hawking Radiation 2": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Ergosphere 3": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Accretion Flow 4": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Relativistic Jet 5": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Event Horizon Telescope 6": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Spaghettification 7": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Quantum Foam 8": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Wormhole Entrance 9": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        },
                                        "Time Dilation Zone 10": {
                                            "metadata": "Level 5",
                                            "children": {}
                                        }
                                    }
                                },
                                "Accretion Disk": {
                                    "metadata": "Level 4",
                                    "children": {
                                        "testb": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        },

                                        "testa": {
                                            "metadata": "Level 4",
                                            "children": {}
                                        }
                                    },

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
                                "testb": {
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
