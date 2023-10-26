"use client";
import Image from 'next/image'

import styles from './page.module.css'

import '@fortawesome/fontawesome-svg-core/styles.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSync } from '@fortawesome/free-solid-svg-icons';
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Home() {
  const messagesCount = 5;
  const refreshAfterTime = 3;
  const [timerValue, timerState] = useState(refreshAfterTime);
  const [totalMessages, totalMessagesState] = useState(0);
  const [failedMessages, failedMessagesState] = useState(0);
  const [avgTimePerMessage, avgTimePerMessageState] = useState("0");


  useEffect(() => {
    const intervalId = setInterval(() => {
      timerState(timerValue-1);
      callAPI();
    }, 1000);
    return () => clearInterval(intervalId);
  }, [timerValue]);

  const callAPI =  () => {
if(timerValue == 0) {
  const fetchData = async () => {
    try {
      timerState(refreshAfterTime);

      const response: any = await axios.get('http://127.0.0.1:5000/monitor');
      console.log(response);
    totalMessagesState(response?.data?.messages_sent);
    failedMessagesState(response?.data?.messages_failed);
    let num = 0.00;
    num = response?.data?.average_time_per_message;
    let val = num.toFixed(2);
    avgTimePerMessageState(val);
    
    } catch (error) {
      console.error('Error fetching data: ', error);
    }
  };

  fetchData();
  
}
  };
  
  return (
    <main className={styles.main}>
      <div className={styles.mainPage}>
        <h2 style={{textAlign: 'center'}}>Monitor</h2>
        <div className='each-row center-place'>
          <div className='refreshRow'>
          <FontAwesomeIcon style= {{height: '2rem', width: '2rem'}} icon={faSync} />
          </div>
          <div>
          Refreshing Time in {timerValue} seconds
          </div>
        </div>
        <div className='each-row'>
          <div className='each-col-1'>
          Total number of messages successful 
          </div>
          <div className='each-col-2'>
          {totalMessages}
          </div>
        </div>
        <div className='each-row'>
          <div className='each-col-1'>
          Total number of messages failed
          </div>
          <div className='each-col-2'>
          {failedMessages}
          </div>
        </div>
        <div className='each-row'>
          <div className='each-col-1'>
          Average number of seconds time per message for successful time
          </div>
          <div className='each-col-2'>
          {avgTimePerMessage}s
          </div>
        </div>
      </div>
    </main>
  )
}
