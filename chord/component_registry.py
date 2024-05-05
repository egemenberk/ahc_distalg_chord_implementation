from adhoccomputing.Generics import Event, EventTypes


def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper


@singleton
class ComponentRegistry:
    """A singleton class that maintains a registry of components."""

    components = {}
    find_successor = 0
    find_predecessor = 0
    closest_preceding_finger = 0

    def get_component_by_instance(self, instance):
        list_of_keys = list()
        list_of_items = self.components.items()
        for item in list_of_items:
            if item[1] == instance:
                list_of_keys.append(item[0])
        return list_of_keys

    def add_component(self, component):
        key = component.componentname + str(component.componentinstancenumber)
        self.components[key] = component

    def get_component_by_key(self, component_name, component_instance_number):
        key = component_name + str(component_instance_number)
        return self.components.get(key)

    def get_arbitrary_component(self, componentname, componentinstancenumber):
        # Return the first component in the registry that is not the same as the one specified
        if len(self.components) == 1:
            return list(self.components.values())[0]
        key = componentname + str(componentinstancenumber)
        for k, v in self.components.items():
            if k != key:
                return v
