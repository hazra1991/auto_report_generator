from io import StringIO
from jinja2 import Environment, FileSystemLoader


class Template:
    def __init__(self,render_on):
        self.RENDER_ON : str = render_on
        self.id_name = None
        self.sublayout_type_indentifier  = None   # differentiate if a same chart type has multiple layout templates in the same file
        self.labels = None
        self.data:list = None
        self.colour = None
        self.heading = None
    
    def __repr__(self) -> str:
        return f"Template({self.__dict__})"



class GenerateTemplate:
    def __init__(self,ENV) -> None:

        self.template_env = Environment(loader=FileSystemLoader(ENV))
    
    def template_2_singleStream(self,template_obj_list):
        buff = StringIO()
        for template_obj in template_obj_list:
            template = self.template_env.get_template(template_obj.RENDER_ON)

            result = template.render(template_obj=template_obj)
            buff.write(result)
            buff.write('\n')
        
        return buff.getvalue()


    def render_and_save(self,temp_obj,save_to_path):
        template = self.template_env.get_template(temp_obj.RENDER_ON)
        result = template.render(template_obj=temp_obj)
        with open(save_to_path,'w') as fd:
            fd.write(result)








