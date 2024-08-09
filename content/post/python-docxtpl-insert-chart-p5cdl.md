---
title: python docxtpl 插入图表
slug: python-docxtpl-insert-chart-p5cdl
url: /post/python-docxtpl-insert-chart-p5cdl.html
date: '2024-08-08 18:02:14+08:00'
lastmod: '2024-08-09 09:06:20+08:00'
toc: true
isCJKLanguage: true
---

# python docxtpl 插入图表

## python-docx 的补丁

首先参考 [python-docx插入可编辑图表 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/701641056) 和 https://github.com/python-openxml/python-docx/pull/392

获得一个猴子补丁，该补丁是使用 python-pptx 的能力来为 python-docx 添加图表

```python
from typing import IO, Union

import docx.oxml
from docx.document import Document as _Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.package import OpcPackage
from docx.opc.packuri import PackURI
from docx.opc.pkgwriter import PackageWriter
from docx.oxml.ns import nsdecls
from docx.oxml.parser import parse_xml
from docx.oxml.shape import CT_GraphicalObjectData, CT_Inline
from docx.oxml.xmlchemy import BaseOxmlElement, ZeroOrOne
from docx.parts.document import DocumentPart
from docx.text.run import Run
from lxml import etree
from pptx.parts.chart import ChartPart as PptChart

# 扩展Document类以添加图表至文档
def add_chart_document(self, chart_type, x, y, cx, cy, chart_data, border: bool = False, style=None, ):
    """
    在文档中添加一个新的图表。

    :param chart_type: 图表类型，来自pptx.enum.chart.XL_CHART_TYPE
    :param x: 图表左上角X坐标
    :param y: 图表左上角Y坐标
    :param cx: 图表宽度
    :param cy: 图表高度
    :param chart_data: 图表数据，ChartData实例
    :param border: 是否显示边框
    :param style: 样式风格
    :return: 创建的图表对象
    """
    run = self.add_paragraph(style=style).add_run()
    chart = run.add_chart(chart_type, x, y, cx, cy, chart_data)
    if not border:
        xml = '<c:spPr><a:ln><a:noFill/></a:ln></c:spPr>'
        parser = etree.XMLParser(recover=True)
        element = etree.fromstring(xml, parser)
        chart._chartSpace.append(element)
    return chart

# 添加方法到Document类
_Document.add_chart = add_chart_document

# 修改OpcPackage类以支持新的part命名规则
def next_partname(self, tmpl):
    """
    修改part名称生成逻辑，适应从PPT到DOCX的转换。
    """
    tmpl = tmpl.replace("/ppt", "/word")  # 更改路径以适应Word文档结构
    partnames = [part.partname for part in self.iter_parts()]
    for n in range(1, len(partnames) + 2):  # 生成唯一的新part名称
        candidate_partname = tmpl % n
        if candidate_partname not in partnames:
            return PackURI(candidate_partname)
    raise Exception("ProgrammingError: ran out of candidate_partnames")

OpcPackage.next_partname = next_partname

# 扩展CT_GraphicalObjectData类以包含图表元素
CT_GraphicalObjectData.cChart = ZeroOrOne("c:chart")

# CT_Inline类增加静态方法用于创建新的图表内联对象
def new_chart(cls, shape_id, rId, x, y, cx, cy):
    """
    创建一个新的图表内联对象。
    """
    inline = parse_xml(cls._chart_xml())  # 解析内联XML模板
    inline.extent.cx = cx  # 设置宽度
    inline.extent.cy = cy  # 设置高度
    chart = CT_Chart.new(rId)  # 创建图表元素
    inline.graphic.graphicData._insert_cChart(chart)  # 将图表元素插入图形数据
    return inline

CT_Inline.new_chart_inline = classmethod(new_chart)

# 提供_chart_xml的静态方法用于生成图表内联XML模板
def _chart_xml(cls):
    """
    返回图表内联元素的XML字符串模板。
    """
    return (
            "<wp:inline %s>\n"
            "  <wp:extent cx='0' cy='0'/>\n"
            '  <wp:effectExtent l="0" t="0" r="0" b="0"/>\n'
            '  <wp:docPr id="1" name="Chart 1"/>\n'
            "  <wp:cNvGraphicFramePr/>\n"
            "  <a:graphic %s>\n"
            '    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/>\n'
            "  </a:graphic>\n"
            "</wp:inline>" % (nsdecls("wp", "a"), nsdecls("a"))
    )

CT_Inline._chart_xml = classmethod(_chart_xml)

# 定义CT_Chart类以处理图表元素
class CT_Chart(BaseOxmlElement):
    @classmethod
    def new(cls, rId):
        """
        创建一个新的图表元素，关联给定的关系ID。
        """
        chart = parse_xml(cls._chart_xml(rId))  # 解析图表XML模板
        chart.id = rId  # 设置关系ID
        return chart

    @classmethod
    def _chart_xml(cls, rId):
        """
        返回图表元素的XML字符串模板。
        """
        return '<c:chart %s r:id="%s"/>\n' % (nsdecls("c", "r"), rId)

docx.oxml.register_element_cls("c:chart", CT_Chart)  # 注册CT_Chart类到oxml解析器

# 扩展DocumentPart类以获取或添加图表
def get_or_add_chart(self, chart_type, x, y, cx, cy, chart_data):
    """
    获取已存在的图表Part，或创建并添加新图表Part。
    """
    chart_part = PptChart.new(chart_type, chart_data, self.package)  # 创建图表Part
    rId = self.relate_to(chart_part, RT.CHART)  # 建立与图表Part的关系
    return rId, chart_part.chart  # 返回关系ID和图表对象

DocumentPart.get_or_add_chart = get_or_add_chart

# 添加新方法以创建新的图表内联对象
def new_chart_inline(self, chart_type, x, y, cx, cy, chart_data):
    """
    创建新的图表内联对象，并关联图表Part。
    """
    rId, chart = self.get_or_add_chart(chart_type, x, y, cx, cy, chart_data)
    shape_id = self.next_id  # 获取下一个形状ID
    return CT_Inline.new_chart_inline(shape_id, rId, x, y, cx, cy), chart

DocumentPart.new_chart_inline = new_chart_inline

# 扩展Run类以直接在运行对象中添加图表
def add_chart(self, chart_type, x, y, cx, cy, chart_data):
    """
    在当前运行对象中添加图表。
    """
    inline, chart = self.part.new_chart_inline(chart_type, x, y, cx, cy, chart_data)
    self._r.add_drawing(inline)  # 将图表内联对象添加到当前运行的绘图元素中
    return chart

Run.add_chart = add_chart

# 修改OpcPackage的保存方法以处理可能的before_marshal异常
def save(self, pkg_file: Union[str, IO[bytes]]):
    """
    保存OPC包到指定的文件路径或二进制流。
    """
    for part in self.parts:
        try:
            part.before_marshal()  # 尝试调用各Part的预处理方法
        except AttributeError:  # 如果Part没有此方法则忽略异常
            pass
    PackageWriter.write(pkg_file, self.rels, self.parts)  # 执行实际的保存操作

OpcPackage.save = save
```

但是该补丁还是需要修改python-docx库 `docx/oxml/shape.py，在类 CT_GraphicalObjectData 中新增属性 cChart = ZeroOrOne('c:chart')

我们可以在这段补丁最上面还未导入库之前添加 import hook，来修改代码（**注意：下面的代码会使调试断点失效**）

```python
import importlib
import importlib.abc
import importlib.util
import os
import sys
from types import ModuleType
import ast

class ClassDefTransformer(ast.NodeTransformer):
    def __init__(self, class_name, attr_name, attr_value):
        self.class_name = class_name
        self.attr_name = attr_name
        self.attr_value = attr_value

    def visit_ClassDef(self, node):
        if node.name == self.class_name:
            # 创建新的属性赋值节点
            new_attr = ast.AnnAssign(
                target=ast.Name(id=self.attr_name, ctx=ast.Store()),
                annotation=ast.Name(id='ZeroOrOne', ctx=ast.Load()),
                value=ast.Call(
                    func=ast.Name(id='ZeroOrOne', ctx=ast.Load()),
                    args=[ast.Constant(value=self.attr_value)],
                    keywords=[]
                ),
                simple=1
            )
            node.body.append(new_attr)
        return node

# 参见 https://stackoverflow.com/a/43573798
class MyMetaFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if path is None or path == "":
            path = [os.getcwd()] # top level import -- 
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                # this module has child modules
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                continue
            if fullname != 'docx.oxml.shape':
                continue
            return importlib.util.spec_from_file_location(fullname, filename, loader=MyLoader(),
                submodule_search_locations=submodule_locations)

        return None # we don't know how to import this

class MyLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None # use default module creation semantics

    def exec_module(self, module: ModuleType):
        # 读取原始模块代码
        with open(module.__file__, 'r', encoding='utf-8') as file:
            code = file.read()
        
        if module.__name__ != 'docx.oxml.shape':
            exec(code, vars(module))
            return

        # 使用 ast 修改 CT_GraphicalObjectData
        # 添加属性 cChart = ZeroOrOne('c:chart')
        # 不采用其他导入后进行 monkeypatch 的方法是因为该类的元类会在类创建时动态添加 _insert_xxx 的方法
        tree = ast.parse(code)
        transformer = ClassDefTransformer("CT_GraphicalObjectData", "cChart", "c:chart")
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree)

        # 获取修改后的代码
        modified_code = compile(modified_tree, filename=module.__file__, mode='exec')

        # 执行修改后的代码
        exec(modified_code, vars(module))

sys.meta_path.insert(0, MyMetaFinder())
```

经过这样的修改，知乎那篇文中的样例应该都可以使用了，并且不用修改上游代码

但是我们还需要在 docxtpl 中使用

## 在 docxtpl 中的使用

经过研究，先直接给出代码

```python
from docx import Document

from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Cm

# 定义图表数据-------------------------------------------------
x = ['A', 'B']
y = [50, 10]

chart_data = ChartData()
chart_data.categories = x
chart_data.add_series(name='数量', values=y)

template_path = os.path.join(config.base_path, 'test.docx')
doc_tpl = DocxTemplate(template_path)
document = doc_tpl.get_docx()
package = document._part.package

paragraph = Document().add_paragraph()
run: Run = paragraph.add_run()

chart_type = XL_CHART_TYPE.COLUMN_CLUSTERED

chart_part = PptChart.new(chart_type, chart_data, package)
rId = package.main_document_part.relate_to(chart_part, RT.CHART)
ct_inline = CT_Inline.new_chart_inline(0, rId, 0, 0, Cm(15), Cm(11))
run._r.add_drawing(ct_inline)

doc_tpl.render({
    'alive_chart': run._r.xml,
})

doc_tpl.save('test_new.docx')
```

其中 test.docx 的内容为

```python
{%r if alive_chart %}
{{ alive_chart }}
{%r endif %}
```

生成出来的内容如图

![Untitled](assets/Untitled-20240808180257-vusbf2n.png)

### 说明

docx 内的图表是分为两部分存储，一部分在主要 document.xml 中，保存了一个 rId 值，对应 charts 资源文件夹下的的 xml，这个xml才是图表的主要内容

资源文件在代码中体现的是 OpcPackage，经过研究，我们使用 `doc_tpl.get_docx()._part.package` 就可以获得

然后我们就可以使用下面两行代码插入chart资源和做出 rId 的关联关系

```python
chart_part = PptChart.new(chart_type, chart_data, package)
rId = package.main_document_part.relate_to(chart_part, RT.CHART)
```

然后再使用

```python
ct_inline = CT_Inline.new_chart_inline(0, rId, 0, 0, Cm(15), Cm(11))
run._r.add_drawing(ct_inline)
```

就在主要 document.xml 中引用该图表了

### 优化

我们也可以参考 `docxtpl.InlineImage` 给出更优化的方案

```python
import typing
from docxtpl import DocxTemplate
from docx.opc.part import XmlPart
from pptx.parts.chart import ChartPart as PptChart
from pptx.chart.data import ChartData
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml.shape import CT_Inline
from pptx.util import Cm, Length, Pt
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION

class InlineChart:
    '''参考 docxtpl.InlineImage 实现
    
    Args:
        chart_type: 图表类型，来自pptx.enum.chart.XL_CHART_TYPE
        chart_data: 图表数据，ChartData实例
        title: 图表标题
        x: 图表左上角X坐标
        y: 图表左上角Y坐标
        cx: 图表宽度
        cy: 图表高度
    '''
    tpl = None
    width = None
    height = None

    def __init__(self, tpl, chart_type, chart_data: ChartData, title='', x: int=0, y: int=0, width: Length=Cm(15), height: Length=Cm(10)):
        self.tpl = tpl
        self.chart_type = chart_type
        self.chart_data = chart_data
        self.title = title
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def _insert_chart(self):
        tpl = typing.cast(DocxTemplate, self.tpl)
        part = typing.cast(XmlPart, tpl.current_rendering_part)
        document = tpl.get_docx()
        package = document._part.package
        chart_part = PptChart.new(self.chart_type, self.chart_data, package)
        # 设置字体
        chart_part.chart.font.size = Pt(10)
        # 设置图例
        chart_part.chart.has_legend = True
        chart_part.chart.legend.position = XL_LEGEND_POSITION.RIGHT
        if self.title:
            # 添加标题
            chart_part.chart.has_title = True
            chart_part.chart.chart_title.text_frame.clear()
            new_title = chart_part.chart.chart_title.text_frame.add_paragraph()
            new_title.text = self.title
        if int(self.chart_type) == int(XL_CHART_TYPE.PIE):
            # 饼图样式修改
            plot = chart_part.chart.plots[0]
            plot.has_data_labels = True    # 显示数据标签
            data_labels = plot.data_labels    # 获取数据标签控制类
            # data_labels.show_category_name = True    # 是否显示类别名称
            data_labels.show_value = False    # 是否显示值
            data_labels.show_percentage = True    # 是否显示百分比
            # 参考 https://answers.microsoft.com/zh-hans/msoffice/forum/all/%E9%A5%BC%E5%9B%BE%E4%B8%AD%E9%9A%90%E8%97%8F/230f831d-ac7f-4467-be1f-fb493c8ea19c
            data_labels.number_format = '[>=0.04]0.0%;;;'    # 标签的数字格式（小于 4% 的不进行展示）
            data_labels.position = XL_LABEL_POSITION.INSIDE_END    # 标签位置
        rId = part.relate_to(chart_part, RELATIONSHIP_TYPE.CHART)
        shape_id = document._part.next_id
        inline: CT_Inline = CT_Inline.new_chart_inline(shape_id, rId, self.x, self.y, self.width, self.height)

        return '</w:t></w:r><w:r><w:drawing>%s</w:drawing></w:r><w:r>' \
               '<w:t xml:space="preserve">' % inline.xml
        
    def __unicode__(self):
        return self._insert_chart()

    def __str__(self):
        return self._insert_chart()

    def __html__(self):
        return self._insert_chart()
```

## 题外

大部分都可以使用 `python-pptx 图表+你想要的关键词` 进行搜索参考实现，下面给出样例

### 图表添加标题

我们搜索 `python pptx 图表标题` 看到

- [python pptx 表格 图表样式详解_python+pptx 设置表格形式-CSDN博客](https://blog.csdn.net/qq_37144341/article/details/107972829)
- [python-pptx 实践 6.1：添加五种基本图形（柱形图、折线图、饼图、条形图、散点图） - 赏尔 - 博客园 (cnblogs.com)](https://www.cnblogs.com/shanger/p/13123701.html)

里面有一段代码是采用 python-pptx 实现的

```python
chart_data = ChartData()
chart_data.categories = ['新闻', '论坛', '微博']
chart_data.add_series(name='负面数', values=[68, 25, 144])
left, top, width, height = Inches(9.5), Inches(2), Inches(15), Inches(15)
graphic_frame = slide.shapes.add_chart(chart_type=XL_CHART_TYPE.PIE,  # 图表类型
                                 x=left, y=top,  # 图表区的位置
                                 cx=width, cy=height,  # 图表的宽和高
                                 chart_data=chart_data)
...
chart = graphic_frame.chart
chart.chart_style = 10	# 图表样式 有1-48种 下方将列出这48种样式
plot = chart.plots[0]
# 设置数据标签
plot.has_data_labels = True  # 显示数据标签
data_labels = plot.data_labels  # 获取数据标签控制类
data_labels.show_category_name = True  # 是否显示类别名称
data_labels.show_value = True  # 是否显示值
data_labels.show_percentage = True  # 是否显示百分比
data_labels.number_format = '0.0%'  # 标签的数字格式
data_labels.position = XL_LABEL_POSITION.INSIDE_END  # 标签位置
chart.font.name = '微软雅黑'
chart.font.size = Pt(10)
chart.font.bold = True
chart.font.color.rgb = RGBColor(255, 255, 255)
# 标题
chart.has_title = True
chart.chart_title.text_frame.clear()
new_title = chart.chart_title.text_frame.add_paragraph()
new_title.text = '各产业平台负面数量、占比'
new_title.font.size = Pt(18)
new_title.font.color.rgb = RGBColor(0, 0, 0)
```

其中的 chart 实际上可以通过我们上面代码中的 `chart_part` 获取到，此处的 chart 就是 `chart_part.chart`

然后我们就可以修改我们的代码来实现自定义图表标题

```python
chart_part = PptChart.new(chart_type, chart_data, package)
chart_part.chart.has_title = True
chart_part.chart.chart_title.text_frame.clear()
new_title = chart_part.chart.chart_title.text_frame.add_paragraph()
new_title.text = '这是一个标题'

rId = package.main_document_part.relate_to(chart_part, RT.CHART)
ct_inline = CT_Inline.new_chart_inline(0, rId, 0, 0, Cm(15), Cm(11))
run._r.add_drawing(ct_inline)

doc_tpl.render({
    'alive_chart': run._r.xml,
})

doc_tpl.save('test_new.docx')

```
