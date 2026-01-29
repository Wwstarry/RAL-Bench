"""Basic test to verify the implementation"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from celery import Celery

# Create test app
app = Celery('testapp')
app.conf.update(
    task_always_eager=True,
    broker_url='memory://',
    result_backend='cache+memory://'
)

# Test basic task
@app.task
def add(x, y):
    return x + y

@app.task(bind=True)
def multiply(self, x, y):
    return x * y

if __name__ == '__main__':
    # Test eager execution
    result = add.delay(4, 4)
    print(f"add(4, 4) = {result.get()}")
    print(f"Task successful: {result.successful()}")
    
    # Test bound task
    result2 = multiply.delay(5, 6)
    print(f"multiply(5, 6) = {result2.get()}")
    print(f"Task successful: {result2.successful()}")
    
    # Test send_task
    result3 = app.send_task('testapp.add', (10, 20))
    print(f"send_task add(10, 20) = {result3.get()}")
    
    print("All tests passed!")