import React from 'react';
import { getCookie } from '../../utils/session/session';
import { useState } from 'react';
import axios from 'axios';

const App = () => {

  const [file, setFile] = useState<File | null>(null);

  const formData = new FormData();
  formData.append('file', file as File);
  formData.append('filename', file?.name as string);

  const csrfToken = getCookie('csrftoken');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    axios({
      method: 'post',
      url: "/api/upload/",
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-CSRFToken': csrfToken
      }
    }).then((response) => {
      console.log(response);
    }
    ).catch((error) => {
      console.log(error);
    }
    );
  }

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    var regex = /(\.csv)$/i;
    if (!regex.exec(event.target.value)) {
      alert('Vous devez sélectionner un fichier se terminant par ".csv" uniquement.');
      event.target.value = '';
      return false;
    } else {
      setFile(event.target.files![0]);
    }
  }

  return (
    <main>
    <h1>BudgetMate</h1>
      <div>
          <form method="POST" onSubmit={handleSubmit}>
            <label htmlFor="file">Sélectionne ton fichier CSV :</label>
            <input type="file" id="csv" name="file" accept=".csv" onChange={handleChange} />
            <br />
            <input type="submit" value="Valider" />
          </form>
      </div>
    </main>
  )
}

export default App;
