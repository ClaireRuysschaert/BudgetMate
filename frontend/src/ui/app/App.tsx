import { useState } from 'react';
import axios from 'axios';

const App = () => {

  const [message, setMessage] = useState<string>('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    axios.get('/api/dummy/').then((response) => {
      setMessage(response.data.message);
    });
  }

  return (
    <main>
    <h1>BudgetMate</h1>
    <div>
        <form method="GET" onSubmit={handleSubmit}>
          <input type="submit" value="Send GET request to /api/dummy/" />
        </form>
        <p>{message}</p>
      </div>
    </main>
  )
}

export default App;
