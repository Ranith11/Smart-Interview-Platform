from reportlab.pdfgen import canvas

c = canvas.Canvas('data/syllabi/Java.pdf')
c.drawString(100, 750, 'Java Syllabus Reference')
c.drawString(100, 700, 'Classes and Objects: Blueprint for creating objects.')
c.drawString(100, 680, 'Inheritance: Inherit properties from parent class.')
c.drawString(100, 660, 'Polymorphism: Perform a single action in different ways.')
c.drawString(100, 640, 'Interfaces: Abstract types used to specify a behavior.')
c.drawString(100, 620, 'Abstract Classes: A restricted class that cannot be used to create objects.')
c.drawString(100, 600, 'Generics: Parameterized types for type safety.')
c.drawString(100, 580, 'Streams: Sequence of elements supporting sequential and parallel operations.')
c.drawString(100, 560, 'Multithreading: Concurrent execution of two or more parts of a program.')
c.save()
print("PDF created.")
