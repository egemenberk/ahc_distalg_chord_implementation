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

    def get_component_by_instance(self, instance):
        """Find keys in the registry that correspond to the input instance."""

        list_of_keys = list()
        list_of_items = self.components.items()
        for item in list_of_items:
            if item[1] == instance:
                list_of_keys.append(item[0])
        return list_of_keys

    def add_component(self, component):
        """Add a component to the registry."""

        key = component.component_name + str(component.component_instance_number)
        self.components[key] = component

    def get_component_by_key(self, component_name, component_instance_number):
        """Retrieve a component from the registry by its key."""

        key = component_name + str(component_instance_number)
        return self.components[key]

    def init(self):
        """Initialize all registered components."""

        for item_key in self.components:
            cmp = self.components[item_key]
            cmp.input_queue.put_nowait(Event(self, EventTypes.INIT, None))