class Material :
    def __init__(self, actor,
                 ambiant=(0.1, 0, 0),
                 diffuse=(0.7, 0, 0),
                 specular=(1,1,1),
                 shininess=100):

        self.actor = actor

        self.ambient = self.actor.GetProperty().GetAmbientColor()
        self.diffuse = self.actor.GetProperty().GetSpecularColor()
        self.specular = self.actor.GetProperty().GetDiffuseColor()
        
        self.shininess = shininess
        
        # self.is