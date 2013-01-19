

MULTI_VALUED_JOINER = "; "

class Metadata(dict):
    
    def copy(self, other):
        self.clear()
        for key, values in other.rawitems():
            self.set(key, values[:])
            
    def update(self,other):
        for name, values in other.rawitems():
            self.set(name, values[:])
            
    def getall(self,name):
        return dict.get(self, name, [])
    
    def get(self, name, default=None):
        values = dict.get(self, name, None)
        if values:
            return MULTI_VALUED_JOINER.join(values)
        else:
            return default
    
    def __getitem__(self, name):
        return self.get(name, u'')
    
    def set(self, name, values):
        dict.__setitem__(self, name, values)
        
    def __setitem__(self, name, values):
        if not isinstance(values, list):
            values = [values]
        values = filter(None, map(unicode, values))
        if len(values):
            self.set(name,values)
        else:
            self.pop(name, None)
            
    def add(self, name, value):
        if value or value == 0:
            self.setdefault(name, []).append(value)
            
    def add_unique(self, name, value):
        if value not in self.getall(name):
            self.add(name, value)
            
    def iteritems(self):
        for name, values in dict.iteritems(self):
            for value in values:
                yield name, value
                
    def items(self):
        return list(self.iteritems())
    
    def rawitems(self):
        return dict.items(self)
    
    def apply_func(self, func):
        for key, values in self.rawitems():
            if not key.startswith("~"):
                self[key] = map(func, values)
                
    def strip_whitespace(self):
        self.apply_func(lambda s: s.strip())